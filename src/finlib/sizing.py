def kelly_fraction(p: float, b: float, cap: float) -> float:
    if p < 0 or p > 1:
        raise ValueError("Input p of kelly_criterion needs to satisfy 0<=p<=1")
    if b <= 0:
        raise ValueError("Input b of kelly_criterion needs to satisfy b>0")
    if cap <= 0:
        raise ValueError("Input cap of kelly_criterion needs to satisfy cap>0")
    return max(min(p - (1 - p) / b, cap), 0)
