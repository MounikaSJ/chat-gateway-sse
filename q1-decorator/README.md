# Dictionary Type Validating decorator

A Python utility decorator to enforce dict[str, int] typing at runtime. Designed to standardize validation across API services and data pipelines.

## Usage

### Running Tests

```bash
python -m unittest tests.py
```

## Files
* decorator.py: Core logic using functools and typing.
* tests.py: Unit tests covering valid inputs, edge cases, and error handling.
