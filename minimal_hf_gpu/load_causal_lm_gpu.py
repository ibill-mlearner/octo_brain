# PyCharm: run this file directly with the interpreter that already has
# the verified CUDA Torch install. Do not reinstall Torch.
# If this interpreter is missing HuggingFace support, install only: transformers safetensors
# This layer only loads a causal language model onto cuda:0.
# No tokenizer, no text generation, no pipeline.

import torch

MODEL_ID = "hf-internal-testing/tiny-random-gpt2"

print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())

if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available")

import transformers.utils as transformers_utils
import transformers.utils.import_utils as transformers_import_utils

# Text-only model load. Some Transformers versions still check optional
# torchvision while importing GPT-2 model code. If a broken or mismatched
# torchvision is installed, that optional vision import can crash with:
# RuntimeError: operator torchvision::nms does not exist
# Do not fix that by touching the working CUDA Torch install. For this layer,
# make Transformers treat optional torchvision as unavailable before importing
# AutoModelForCausalLM.
transformers_utils.is_torchvision_available = lambda: False
transformers_import_utils.is_torchvision_available = lambda: False

from transformers import AutoModelForCausalLM

# Use a tiny causal LM repo that has model.safetensors. This avoids the
# Transformers torch.load safety block on Torch 2.5.1 while preserving the
# working CUDA Torch install.
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, use_safetensors=True)
model.to("cuda")
model.eval()

print(next(model.parameters()).device)
print(model.__class__.__name__)
