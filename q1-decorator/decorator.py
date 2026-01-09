import functools
from typing import Any, Callable, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")

def validate_dict_types(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator that ensures all dictionary arguments passed to the wrapped function 
    conform to the dict[str, int] type hint. [cite: 19]
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        # Validate positional arguments
        for arg in args:
            if isinstance(arg, dict):
                _check_schema(arg)
        
        # Validate keyword arguments 
        for value in kwargs.values():
            if isinstance(value, dict):
                _check_schema(value)
                
        return func(*args, **kwargs)
    
    return wrapper

def _check_schema(data: dict[Any, Any]) -> None:
    """Internal helper to verify keys are strings and values are integers. [cite: 15, 19]"""
    for key, val in data.items():
        if not isinstance(key, str):
            raise TypeError(
                f"Invalid key type: {type(key).__name__}. "
                f"Expected 'str' for dict[str, int]."
            )
        if not isinstance(val, int):
            raise TypeError(
                f"Invalid value type: {type(val).__name__}. "
                f"Expected 'int' for dict[str, int]."
            )
