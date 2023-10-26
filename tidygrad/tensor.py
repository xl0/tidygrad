# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_tensor.ipynb.

# %% auto 0
__all__ = ['Tensor', 'BaseOp', 'BinaryElementwiseOp', 'UnaryElementwiseOp']

# %% ../nbs/01_tensor.ipynb 2
import numpy as np
from lovely_numpy import lovely


class Tensor:
    ...

# %% ../nbs/01_tensor.ipynb 3
def calculate_target_shape(s1, s2):
    """Calculate the target shape for broadcasting two tensors"""

    # expand shaped to be the same length. Note (1,) * <negative> is empty
    s2 = (1,) * (len(s1) - len(s2)) + s2
    s1 = (1,) * (len(s2) - len(s1)) + s1

    out_shape = ()
    for dims in list(zip(reversed(s1), reversed(s2))):
        if dims[0] != 1 and dims[1] != 1 and dims[0] != dims[1]:
            raise ValueError(f"Cannot broadcast {s1} and {s2}")
        out_shape = (max(dims),) + out_shape

    return out_shape

# %% ../nbs/01_tensor.ipynb 4
def maybe_broadcast_elementwise(a: Tensor, b: Tensor):
    """Broadcast two tensors if they have different shapes"""
    if a.data.shape != b.data.shape:
        target_shape = calculate_target_shape(a.data.shape, b.data.shape)
        # print(
        #     f"Elementwise broadcasted {a.data.shape} and {b.data.shape} to {target_shape}"
        # )
        a = a.broadcast(target_shape) if a.data.shape != target_shape else a
        b = b.broadcast(target_shape) if b.data.shape != target_shape else b

    return a, b


def maybe_broadcast_matmul(a: Tensor, b: Tensor):
    """Broadcast two tensors if they have different shapes, except for the last two dimensions"""

    a_short_shape = a.data.shape[:-2]
    b_short_shape = b.data.shape[:-2]

    if a_short_shape != b_short_shape:
        target_shape = calculate_target_shape(a_short_shape, b_short_shape)
        # print(
        #     f"Matmul broadcasted {a.data.shape} and {b.data.shape} to {target_shape + a.data.shape[-2:]} and {target_shape + b.data.shape[-2:]}"
        # )
        a = (
            a.broadcast(target_shape + a.data.shape[-2:])
            if a_short_shape != target_shape
            else a
        )
        b = (
            b.broadcast(target_shape + b.data.shape[-2:])
            if b_short_shape != target_shape
            else b
        )

    return a, b

# %% ../nbs/01_tensor.ipynb 5
class BaseOp:
    """Base class for all operations"""

    name_template = "??"

    def __init__(self, *args, name: str = None):
        assert isinstance(
            name, (str, type(None))
        ), f"name= should be str, got {type(name)}. You probably meant something else."

        self.args = [
            arg
            if isinstance(arg, Tensor)
            else Tensor(data=np.asarray(arg, dtype=np.float32))
            for arg in args
        ]
        self.name = (
            self.name_template.format(*[arg.name for arg in self.args])
            if name is None
            else name
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({', '.join([str(arg) for arg in self.args])})"
        )


class BinaryElementwiseOp(BaseOp):
    """Base class for binary elementwise operations"""

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.parents = self.args = maybe_broadcast_elementwise(*self.args)


class UnaryElementwiseOp(BaseOp):
    """Base class for unary elementwise operations"""

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        self.parents = self.args

# %% ../nbs/01_tensor.ipynb 6
class Load(BaseOp):
    """Load a tensor"""

    name_template = "?"

    def __init__(self, name=None):
        super().__init__(name=name)
        self.parents = []


class Add(BinaryElementwiseOp):
    """Add two tensors"""

    name_template = "({}+{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.out = Tensor(
            data=self.args[0].data + self.args[1].data, name=self.name, op=self
        )

    def backward(self):
        self.parents[0].grad += self.out.grad
        self.parents[1].grad += self.out.grad


class Sub(BinaryElementwiseOp):
    """Subtract two tensors"""

    name_template = "({}-{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.out = Tensor(
            data=self.args[0].data - self.args[1].data, name=self.name, op=self
        )

    def backward(self):
        self.parents[0].grad += self.out.grad
        self.parents[1].grad -= self.out.grad


class Mul(BinaryElementwiseOp):
    """Multiply two tensors"""

    name_template = "({}*{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.out = Tensor(
            data=self.args[0].data * self.args[1].data, name=self.name, op=self
        )

    def backward(self):
        self.parents[0].grad += self.out.grad * self.parents[1].data
        self.parents[1].grad += self.out.grad * self.parents[0].data


class Div(BinaryElementwiseOp):
    """Divide two tensors"""

    name_template = "({}/{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.out = Tensor(
            data=self.args[0].data / self.args[1].data, name=self.name, op=self
        )

    def backward(self):
        self.parents[0].grad += self.out.grad / self.parents[1].data
        self.parents[1].grad -= (
            self.out.grad * self.parents[0].data / (self.parents[1].data ** 2)
        )


class Neg(UnaryElementwiseOp):
    """Negate a tensor"""

    name_template = "(-{})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        self.out = Tensor(-self.args[0].data, name=self.name, op=self)

    def backward(self):
        self.parents[0].grad -= self.out.grad


class Log(UnaryElementwiseOp):
    """Take the natural logarithm of a tensor"""

    name_template = "log({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)

        self.out = Tensor(np.log(self.args[0].data), name=self.name, op=self)

    def backward(self):
        self.parents[0].grad += self.out.grad / self.parents[0].data


class Exp(UnaryElementwiseOp):
    """Exponentiate a tensor"""

    name_template = "exp({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)

        self.out = Tensor(np.exp(self.args[0].data), name=self.name, op=self)

    def backward(self):
        self.parents[0].grad += self.out.grad * self.out.data


class Matmul(BaseOp):
    """Matrix multiplication of two tensors"""

    name_template = "({}@{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.parents = self.args = maybe_broadcast_matmul(*self.args)
        self.out = Tensor(
            np.matmul(self.args[0].data, self.args[1].data),
            name=self.name,
            op=self,
        )

    def backward(self):
        self.parents[0].grad += np.matmul(
            self.out.grad, self.parents[1].data.swapaxes(-1, -2)
        )
        self.parents[1].grad += np.matmul(
            self.parents[0].data.swapaxes(-1, -2), self.out.grad
        )


class Sum(BaseOp):
    """Sum a tensor along the given axis (int or tuple of ints)"""

    name_template = "sum({})"

    def __init__(self, a, name=None, axis=None, keepdims=False):
        super().__init__(a, name=name)
        # self.axis = axis
        self.parents = self.args
        self.out = Tensor(
            np.sum(self.args[0].data, axis=axis, keepdims=keepdims),
            name=self.name,
            op=self,
        )

    def backward(self):
        self.parents[0].grad += self.out.grad


class Broadcast(BaseOp):
    """Broadcast a tensor to the given shape"""

    name_template = "broadcast({})"

    def __init__(self, a, target_shape, name=None):
        super().__init__(a, name=name)
        self.target_shape = target_shape
        self.parents = self.args
        self_shape = self.args[0].data.shape
        assert self_shape != target_shape, "Why are you broadcasting to the same shape?"

        if len(self_shape) < len(target_shape):
            expanded_shape = (len(target_shape) - len(self_shape)) * (1,) + self_shape
        else:
            expanded_shape = self_shape

        final_shape = ()
        broadcasted_dims = ()

        for s_expanded, s_target in reversed(list(zip(expanded_shape, target_shape))):
            if s_expanded != s_target:
                if s_expanded != 1:
                    raise ValueError(f"Cannot broadcast {self_shape} to {target_shape}")
                else:
                    broadcasted_dims = (True,) + broadcasted_dims
                    final_shape = (s_target,) + final_shape
            else:
                broadcasted_dims = (False,) + broadcasted_dims
                final_shape = (s_expanded,) + final_shape

        broadcasted_data = np.broadcast_to(self.args[0].data, final_shape)

        assert final_shape == broadcasted_data.shape

        data = broadcasted_data
        self.broadcasted_dims = broadcasted_dims

        self.out = Tensor(data, name=self.name, op=self)

    def backward(self):
        axis = tuple([i for i, dim in enumerate(self.broadcasted_dims) if dim])
        summed = self.out.grad.sum(axis=axis, keepdims=True)

        if summed.shape != self.parents[0].data.shape:
            summed = summed.reshape(self.parents[0].data.shape)

        self.parents[0].grad += summed


# class LessThan(BinaryElementwiseOp):
#     name_template = "({}<{})"

#     def __init__(self, a, b, name=None):
#         super().__init__(a, b, name=name)
#         self.out = Tensor(
#             data=self.args[0].data < self.args[1].data, name=self.name, op=self
#         )

#     # def backward(self):
#     #     self.parents[0].grad += self.out.grad * (self.parents[0].data < self.parents[1].data)
#     #     self.parents[1].grad += self.out.grad * (self.parents[0].data >= self.parents[1].data)

# class Where(BaseOp):
#     name_template = "where({})"

#     def __init__(self, a, b, c, name=None):
#         super().__init__(a, b, c, name=name)
#         self.parents = self.args
#         self.out = Tensor(
#             data=np.where(self.args[0].data, self.args[1].data, self.args[2].data),
#             name=self.name,
#             op=self,
#         )

#     def backward(self):
#         # self.parents[0].grad += self.out.grad * self.parents[1].data
#         # self.parents[0].grad += self.out.grad * self.parents[2].data

#         self.parents[1].grad += self.out.grad * self.parents[0].data
#         self.parents[2].grad += self.out.grad * (1 - self.parents[0].data)


class ExpLog(UnaryElementwiseOp):
    """Exponentiate a tensor"""

    name_template = "exp({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)

        def logexp(x):
            return np.where(x < 0, np.log(1 + np.exp(x)), x + np.log(1 + np.exp(-x)))

        self.out = Tensor(logexp(self.args[0].data), name=self.name, op=self)

    def backward(self):
        self.parents[0].grad += self.out.grad * (
            1 - 1 / (1 + np.exp(self.parents[0].data))
        )

# %% ../nbs/01_tensor.ipynb 8
class Tensor:
    # op = "L"
    name: str = ""

    def __init__(self, data, name=None, op=None, eps=1e-8):
        self.data = np.asarray(data)
        self.grad = np.zeros_like(self.data, dtype=np.float32)
        self.eps = eps
        self.op = op or Load(name=name)
        self.name = name or self.op.name

    def __repr__(self):
        value_str = f"v={lovely(self.data)}"
        grad_str = f"∇={lovely(self.grad)}"
        parents = (
            f" parents=[" + ",".join([p.name for p in self.op.parents]) + "]"
            if self.op.parents
            else ""
        )
        return f'Tensor{list(self.data.shape)}(name="{self.name}" op={type(self.op).__name__}{parents}):\n    {value_str}\n    {grad_str}'

    def broadcast(self, target_shape, name=None):
        return Broadcast(self, target_shape, name=name).out

    def add(self, other, name=None):
        return Add(self, other, name=name).out

    def sub(self, other, name=None):
        return Sub(self, other, name=name).out

    def mul(self, other, name=None):
        return Mul(self, other, name=name).out

    def div(self, other, name=None):
        return Div(self, other, name=name).out

    def neg(self, name=None):
        return Neg(self, name=name).out

    def log(self, name=None):
        return Log(self, name=name).out

    def exp(self, name=None):
        return Exp(self, name=name).out

    def mmul(self, other, name=None):
        return Matmul(self, other, name=name).out

    def sum(self, name=None, axis=None, keepdims=False):
        return Sum(self, name=name, axis=axis, keepdims=keepdims).out

    def mean(self, name=None, axis=None, keepdims=False):
        reduced = np.prod(self.data.shape)
        if axis:
            reduced = np.prod([self.data.shape[i] for i in axis])
        return Sum(self, name=name, axis=axis, keepdims=keepdims).out / reduced

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

    def equal(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        return self.data == other.data

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
                if p not in visited:
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
        self.grad.fill(0)
