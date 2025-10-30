from micropython import const


def _only_digits(val: str):
    return all(c in '0123456789' for c in val)


def gtin_control_digit(code: str):
    if not _only_digits(code):
        raise ValueError('Invalid code')
    return str((10 - sum(
        int(c) * (1 if i % 2 else 3) for i, c in enumerate(reversed(code))
    ) % 10) % 10)


def gs1_retail_weight_code_gen(product: str, weight: str):
    if len(product) != 5 or not _only_digits(product):
        raise ValueError('Invalid product code')
    if len(weight) != 5 or not _only_digits(weight):
        raise ValueError('Invalid weight code')
    code = f'28{product}{weight}'
    return code + gtin_control_digit(code)
