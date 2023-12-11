# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_tensor.ipynb.

# %% auto 0
__all__ = ['Tensor']

# %% ../nbs/01_tensor.ipynb 2
import numpy as np
from lovely_numpy import lovely

import tidygrad.ops as ops
import tidygrad.tensor_helpers as helpers

# %% ../nbs/01_tensor.ipynb 3
class no_grad:
    def __enter__(self):
        self.old_grad = ops.common._grad
        ops.common._grad = False
        return self

    def __exit__(self, *args):
        ops.common._grad = self.old_grad

# %% ../nbs/01_tensor.ipynb 4
_num_tensors = 0


class Tensor:
    pass


class Tensor:
    # op = "L"
    name: str = ""

    def __init__(self, data, name=None, op=None, eps=1e-8, requires_grad=False):
        global _num_tensors
        _num_tensors += 1
        self.data = np.asarray(data)

        self.grad = (
            np.zeros_like(self.data, dtype=np.float32) if requires_grad else None
        )
        self.eps = eps
        self.op = op or ops.Load(name=name)
        self.name = name or self.op.name
        self.requires_grad = requires_grad

    def __repr__(self):
        value_str = f"v={lovely(self.data)}"
        grad_str = f"∇={lovely(self.grad)}" if self.grad is not None else ""
        parents = (
            f" parents=[" + ",".join([p.name for p in self.op.parents]) + "]"
            if self.op.parents
            else ""
        )
        # name="{self.name}
        return f'Tensor{list(self.data.shape)}(" op={type(self.op).__name__}{parents}):\n    {value_str}\n    {grad_str}'

    def accum_grad(self, grad):
        if not self.requires_grad:
            return

        if self.grad is None:
            self.grad = grad
        else:
            self.grad += grad

    def broadcast(self, target_shape, name=None):
        return ops.Broadcast(self, target_shape, name=name).out

    def add(self, other, name=None):
        return ops.Add(self, other, name=name).out

    def sub(self, other, name=None):
        return ops.Sub(self, other, name=name).out

    def mul(self, other, name=None):
        return ops.Mul(self, other, name=name).out

    def div(self, other, name=None):
        return ops.Div(self, other, name=name).out

    def neg(self, name=None):
        return ops.Neg(self, name=name).out

    def pow(self, power, name=None):
        return ops.Pow(self, power, name=name).out

    def log(self, name=None):
        return ops.Log(self, name=name).out

    def exp(self, name=None):
        return ops.Exp(self, name=name).out

    def mmul(self, other, name=None):
        return ops.Matmul(self, other, name=name).out

    def sum(self, name=None, axis=None, keepdims=False):
        return ops.Sum(self, name=name, axis=axis, keepdims=keepdims).out

    def transpose(
        self,
        dim0: int,
        dim1: int,
        name=None,
    ):
        return ops.Transpose(
            self,
            dim0,
            dim1,
            name=name,
        ).out

    # def softmax(input, name=None):
    #     return func.softmax(input, name=name)

    def mean(self, name=None, axis=None, keepdims=False):
        return helpers.mean(self, name=name, axis=axis, keepdims=keepdims)

    def std(self, name=None, axis=None, keepdims=False, correction=1):
        return helpers.std(
            self, name=name, axis=axis, keepdims=keepdims, correction=correction
        )

    def split(self, n, axis=0):
        return helpers.split(self, n, axis=axis)

    # def lt(self, other, name=None):
    #     return LessThan(self, other, name=name).out

    # def where(self, other1, other2, name=None):
    #     return Where(self, other1, other2, name=name).out

    def __add__(self, other):
        return self.add(other)

    def __radd__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.sub(other)

    def __rsub__(self, other):
        return -(self.sub(other))

    def __mul__(self, other):
        return self.mul(other)

    def __rmul__(self, other):
        return self.mul(other)

    def __truediv__(self, other):
        return self.div(other)

    def __neg__(self):
        return self.neg()

    def __pow__(self, power):
        return self.pow(power)

    def equal(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        return self.data == other.data

    def __getitem__(self, key):
        return ops.Slice(self, key).out

    # def __setitem__(self, key, value):
    #     return SetSlice(self, key, value)

    @property
    def shape(self):
        return self.data.shape

    # def __lt__(self, other):
    #     return self.lt(other)

    def backward(self):
        # Create a list of all parent nodes, in reverse order
        # Start with the current node
        visited = []
        nodes = []

        assert self.data.size == 1, "Cannot call backward on non-scalar tensor"

        def walk(node):
            for p in node.op.parents:
                if p not in visited and p.requires_grad:
                    visited.append(p)
                    walk(p)
                    nodes.append(p)

        walk(self)
        nodes.append(self)

        # print(nodes)
        self.grad = np.ones_like(self.data)
        for n in nodes[::-1]:
            if hasattr(n.op, "backward"):
                n.op.backward()

    def zero_grad(self):
        assert self.requires_grad, "Cannot zero grad on non-differentiable tensor"
        self.grad.fill(0)
