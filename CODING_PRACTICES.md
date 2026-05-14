# Coding Practices

This file records the project owner's preferred coding style and design hygiene for future code changes. It is not meant to restate basic Python conventions. Instead, it captures the personal readability rules that should guide how code is shaped in this repository.

## Method and function signatures

Prefer vertical, list-like argument formatting for method and function definitions, especially when a signature includes multiple arguments, type hints, or a return type.

Instead of keeping every argument in one long line:

```python
def execute(self, action: torch.Tensor, device: torch.device, dtype: torch.dtype) -> ActionResult:
    ...
```

Prefer putting each input argument on its own line:

```python
def execute(
    self,
    action: torch.Tensor,
    device: torch.device,
    dtype: torch.dtype,
) -> ActionResult:
    ...
```

This should read like a vertical list of inputs. In PyCharm, pressing return inside the argument list should naturally continue the next argument on a new, properly indented line.

## Readability goal

The goal is to make signatures easy to scan visually. Long linear signatures can become hard to read when they include `self`, domain objects, device parameters, dtype parameters, and return annotations. Treat each argument as its own item so the expected inputs are clear before reading the method body.

## Preferred shape for growing code

When adding or expanding methods:

- Use the vertical signature style once the method has more than a couple of inputs or includes detailed type annotations.
- Keep the return annotation attached to the closing parenthesis line.
- Let the method body begin on the next line, indented normally.
- Favor this style for new code even if nearby older code has not been refactored yet.

This mirrors the project owner's preferred editing flow: open the definition, place each input on its own line, and let the editor maintain the indentation so the signature reads cleanly as a structured list.
