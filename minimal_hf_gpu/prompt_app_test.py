# PyCharm: run this file directly after load_causal_lm_gpu.py works.
# This is the next layer only: a minimal GPU prompting app.
# No pipeline, no server, no UI, no unrelated packages.

MODEL_ID = "distilbert/distilgpt2"


class GpuPromptApp:
    def __init__(self):
        import torch

        self.torch = torch

        print(torch.__version__)
        print(torch.version.cuda)
        print(torch.cuda.is_available())

        if not torch.cuda.is_available():
            raise SystemExit("CUDA is not available")

        import transformers.utils as transformers_utils
        import transformers.utils.import_utils as transformers_import_utils

        transformers_utils.is_torchvision_available = lambda: False
        transformers_import_utils.is_torchvision_available = lambda: False

        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            use_safetensors=True,
        )
        self.model.to("cuda")
        self.model.eval()

        print(next(self.model.parameters()).device)
        print(self.model.__class__.__name__)

    def prompt(self, text):
        inputs = self.tokenizer(text, return_tensors="pt").to("cuda")

        with self.torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=40,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)


if __name__ == "__main__":
    app = GpuPromptApp()
    print(app.prompt("The GPU is running an AI model because"))
