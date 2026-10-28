from __future__ import annotations

import math


def evaluate(family: str, parameters: dict[str, float], x: float) -> float:
    """Allowlisted lesson functions. This does not evaluate expression strings."""
    if family == "sine":
        return parameters["A"] * math.sin(parameters["B"] * x + parameters["C"]) + parameters["D"]
    if family == "linear":
        return parameters["A"] * x + parameters["B"]
    if family == "quadratic":
        return parameters["A"] * x * x + parameters["B"] * x + parameters["C"]
    raise ValueError(f"Unsupported function family: {family}")


def samples(family: str, parameters: dict[str, float], x_min: float, x_max: float, count: int) -> list[float]:
    if count < 2 or x_min >= x_max:
        raise ValueError("Invalid sample domain.")
    step = (x_max - x_min) / (count - 1)
    return [evaluate(family, parameters, x_min + index * step) for index in range(count)]
