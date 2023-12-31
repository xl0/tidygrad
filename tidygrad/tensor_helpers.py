# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_tensor_helpers.ipynb.

# %% auto 0
__all__ = ['Tensor', 'mean', 'std', 'split']

# %% ../nbs/01_tensor_helpers.ipynb 2
import numpy as np
import tidygrad.ops as ops

# %% ../nbs/01_tensor_helpers.ipynb 3
class Tensor:
    pass


def mean(input: Tensor, name=None, axis=None, keepdims=False) -> Tensor:
    reduced = np.prod(input.data.shape)
    if isinstance(axis, int):
        axis = (axis,)
    if axis:
        reduced = np.prod([input.data.shape[i] for i in axis])
    return ops.Sum(input, name=name, axis=axis, keepdims=keepdims).out / reduced


def std(input: Tensor, name=None, axis=None, keepdims=False, correction=1) -> Tensor:
    if isinstance(axis, int):
        axis = (axis,)
    v1 = input - input.mean(axis=axis, keepdims=True)
    var = v1**2

    if axis is None:
        numel = np.prod(input.data.shape)
    else:
        numel = np.prod([input.data.shape[i] for i in axis])
    assert numel > correction, "Cannot compute std of a single value"

    res = (var.sum(axis=axis, keepdims=keepdims) / (numel - correction)).pow(0.5)
    if name is not None:
        res.name = name
    return res


def split(t: Tensor, n: int, axis: int):
    step = t.shape[axis] // n
    assert step * n == t.shape[axis], "Can't split tensor evenly"

    chunks = []

    key = [slice(None)] * len(t.shape)
    for i in range(n):
        start = i * step
        end = (i + 1) * step
        key[axis] = slice(start, end)
        chunks.append(t[tuple(key)])

    return chunks
