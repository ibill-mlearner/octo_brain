import os
import time
import warnings

MODEL_ID = "microsoft/Phi-3-mini-4k-instruct"
DURATION_SECONDS = 65
BATCH_SIZE = 2
SEQUENCE_TOKENS = 1024
WORK_SECONDS = 0.35
SLEEP_SECONDS = 0.02

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*cache-system uses symlinks.*")


# This is the next test after prompt_app_test_2.py. Test 2 proved that repeated
# GPU inference works, but the model was still small enough that the RTX 4060 Ti
# was not being pushed very hard. This file keeps the same basic structure and
# the same Windows/PyCharm fixes, but swaps in a much larger causal LM so just
# keeping the model resident on cuda:0 is a real GPU memory and compute step.
class LargeGpuPromptStressTest:
    def __init__(self):
        import torch

        self.torch = torch

        print(torch.__version__)
        print(torch.version.cuda)
        print(torch.cuda.is_available())

        if not torch.cuda.is_available():
            raise SystemExit("CUDA is not available")

        print(torch.cuda.get_device_name(0))

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

        # Phi-3 Mini is 3.8B parameters. Loading it as float16 puts it in the
        # rough 8GB VRAM class instead of accidentally doubling that with float32.
        # use_safetensors=True keeps the earlier Torch 2.5.1 safety issue out of
        # the path, and low_cpu_mem_usage is intentionally not used because that
        # would require adding accelerate.
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            use_safetensors=True,
            trust_remote_code=True,
        )
        self.model.to("cuda")
        self.model.eval()

        print(next(self.model.parameters()).device)
        print(next(self.model.parameters()).dtype)
        print(self.model.__class__.__name__)
        print(f"allocated_gb={torch.cuda.memory_allocated() / 1024**3:.2f}")
        print(f"reserved_gb={torch.cuda.memory_reserved() / 1024**3:.2f}")

        prompt = "The RTX 4060 Ti is running a larger language model on CUDA. " * 80
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

        print("starting larger gpu stress")

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
    test = LargeGpuPromptStressTest()
    test.run()
