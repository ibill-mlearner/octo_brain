import os
import time
import warnings

MODEL_ID = "distilbert/distilgpt2"

# The target is moderate pressure, not maximum pressure. A 4060 Ti can run this
# model easily, so the script uses a simple duty cycle: short GPU work bursts,
# then short sleeps. If Task Manager shows utilization too low or too high, tune
# only WORK_SECONDS, SLEEP_SECONDS, BATCH_SIZE, or SEQUENCE_TOKENS below. Do not
# change the install, do not change Torch, and do not add new layers just to tune
# load.
DURATION_SECONDS = 65
BATCH_SIZE = 64
SEQUENCE_TOKENS = 384
WORK_SECONDS = 0.20
SLEEP_SECONDS = 0.02

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*cache-system uses symlinks.*")


# This file exists because the previous layers finally proved the GPU path works:
# first raw Torch CUDA tensors worked, then HuggingFace loaded a causal language
# model onto cuda:0, then the prompt app generated text from the GPU. The point
# of this file is not troubleshooting and not architecture. It is the next small
# layer: keep one causal language model resident on the NVIDIA GPU and repeatedly
# run inference for at least one minute.
class GpuPromptStressTest:
    def __init__(self):
        import torch

        self.torch = torch

        print(torch.__version__)
        print(torch.version.cuda)
        print(torch.cuda.is_available())

        if not torch.cuda.is_available():
            raise SystemExit("CUDA is not available")

        # The important fixes from the earlier files are kept here because they were the
        # actual things that made this Windows/PyCharm stack work. The working Torch
        # install is torch 2.5.1+cu121, so this file does not reinstall or upgrade Torch.
        # Transformers is forced away from optional torchvision checks because the local
        # torchvision install can crash on the missing torchvision::nms operator even
        # though this is a text-only model. The model load also uses safetensors so it
        # does not go through the blocked torch.load path on Torch 2.5.1.
        import transformers.utils as transformers_utils
        import transformers.utils.import_utils as transformers_import_utils

        transformers_utils.is_torchvision_available = lambda: False
        transformers_import_utils.is_torchvision_available = lambda: False

        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers.utils import logging as transformers_logging

        transformers_logging.set_verbosity_error()

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            use_safetensors=True,
        )
        self.model.to("cuda")
        self.model.eval()

        print(next(self.model.parameters()).device)
        print(self.model.__class__.__name__)
        print(torch.cuda.get_device_name(0))

        # This is deliberately not a chatbot UI. It does not print generated responses,
        # does not use transformers.pipeline, does not run a server, and does not add
        # unrelated packages. It loads the same small real causal LM used by the first
        # prompt app, prepares one repeated prompt batch on cuda, and then runs forward
        # passes. That is enough to exercise the AI model on the GPU without mixing in a
        # bunch of application code.
        prompt = "The GPU is running an AI model. " * 40
        inputs = self.tokenizer(
            [prompt] * BATCH_SIZE,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=SEQUENCE_TOKENS,
        ).to("cuda")

        self.input_ids = inputs["input_ids"]
        self.attention_mask = inputs["attention_mask"]

        print(self.input_ids.shape)

    def run(self):
        torch = self.torch
        end_time = time.perf_counter() + DURATION_SECONDS
        next_status_time = time.perf_counter() + 10
        passes = 0

        print("starting gpu stress")

        # Expected successful signs are boring: torch/CUDA prints, cuda:0 prints for the
        # model, then a few progress lines for about one minute, then a clean exit. The
        # script synchronizes CUDA during the loop so the timing reflects real GPU work
        # instead of only queueing kernels on the CPU and exiting early.
        with torch.inference_mode():
            while time.perf_counter() < end_time:
                work_until = time.perf_counter() + WORK_SECONDS

                while time.perf_counter() < work_until:
                    self.model(
                        input_ids=self.input_ids,
                        attention_mask=self.attention_mask,
                        use_cache=False,
                    )
                    torch.cuda.synchronize()
                    passes += 1

                remaining = end_time - time.perf_counter()
                if remaining <= 0:
                    break

                time.sleep(min(SLEEP_SECONDS, remaining))

                if time.perf_counter() >= next_status_time:
                    seconds_left = max(0, int(end_time - time.perf_counter()))
                    allocated_gb = torch.cuda.memory_allocated() / 1024**3
                    reserved_gb = torch.cuda.memory_reserved() / 1024**3
                    print(
                        f"passes={passes} "
                        f"seconds_left={seconds_left} "
                        f"allocated_gb={allocated_gb:.2f} "
                        f"reserved_gb={reserved_gb:.2f}"
                    )
                    next_status_time += 10

        torch.cuda.synchronize()
        print(f"done passes={passes}")


if __name__ == "__main__":
    test = GpuPromptStressTest()
    test.run()
