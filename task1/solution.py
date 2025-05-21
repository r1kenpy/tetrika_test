from functools import wraps
from inspect import get_annotations

RETURN_TYPE_ERROR_MESSAGE = (
    "Неправильный тип данных. "
    "Должно вернуться: {return_type}. Возвращается: {result_type}"
)
ERROR_MESSAGE = (
    "Неправильный тип данных. "
    "Ожидается: {expected_type}, а передан {type_value}"
)


def strict(func):
    @wraps(func)
    def wrapper(*args):
        annotations = get_annotations(func)
        return_type = (
            annotations.pop("return")
            if annotations.get("return", None) is not None
            else None
        )
        for i, expected_type in enumerate(annotations.values()):
            value = args[i]
            type_value = type(value)
            if not (type_value is expected_type):
                raise TypeError(
                    ERROR_MESSAGE.format(
                        expected_type=expected_type, type_value=type_value
                    )
                )

        res = func(*args)
        result_type = type(res)
        if return_type is not None and not (result_type is return_type):
            raise TypeError(
                RETURN_TYPE_ERROR_MESSAGE.format(
                    return_type=return_type, result_type=result_type
                )
            )
        return res

    return wrapper


@strict
def sum_two(a: int, b: int) -> int:
    return a + b
