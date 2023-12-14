# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/02_ops.common.ipynb.

# %% auto 0
__all__ = ['BaseOp', 'BinaryElementwiseOp', 'UnaryElementwiseOp', 'Load', 'Add', 'Sub', 'Mul', 'Div', 'Neg', 'Pow', 'Log', 'Exp',
           'ExpLog', 'Matmul', 'Sum', 'Broadcast', 'Slice', 'Transpose', 'Dropout', 'Embedding']

# %% ../../nbs/02_ops.common.ipynb 2
import numpy as np

_grad = True

# %% ../../nbs/02_ops.common.ipynb 3
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

# %% ../../nbs/02_ops.common.ipynb 4
def maybe_broadcast_elementwise(a, b):
    """Broadcast two tensors if they have different shapes"""
    if a.data.shape != b.data.shape:
        target_shape = calculate_target_shape(a.data.shape, b.data.shape)
        # print(
        #     f"Elementwise broadcasted {a.data.shape} and {b.data.shape} to {target_shape}"
        # )
        a = a.broadcast(target_shape) if a.data.shape != target_shape else a
        b = b.broadcast(target_shape) if b.data.shape != target_shape else b

    return a, b


def maybe_broadcast_matmul(a, b):
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

# %% ../../nbs/02_ops.common.ipynb 7
_num_ops = 0


class BaseOp:
    """Base class for all operations"""

    name_template = "??"

    # out: Tensor

    def __init__(self, *args, name: str = None):
        from tidygrad.tensor import Tensor

        global _num_ops
        _num_ops += 1
        assert isinstance(
            name, (str, type(None))
        ), f"name= should be str, got {type(name)}. You probably meant something else."

        self.args = [
            arg
            if isinstance(arg, Tensor)
            else Tensor(data=np.asarray(arg, dtype=np.float32))
            for arg in args
        ]
        self.name = ""  # (self.name_template.format(*[arg.name for arg in self.args]) if name is None else name)
        self.requires_grad = any(arg.requires_grad for arg in self.args) and _grad
        self.parents = []

    def set_out(self, data):
        from tidygrad.tensor import Tensor

        op = self if self.requires_grad else None
        self.out = Tensor(
            data=data, requires_grad=self.requires_grad, name=self.name, op=op
        )

    def check_backward(self):
        # Add more checks here?
        assert (
            self.out.requires_grad
        ), f"You are trying to backpropagate through a non-differentiable operation:\n{self}"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({', '.join([str(arg) for arg in self.args])})"
        )


class BinaryElementwiseOp(BaseOp):
    """Base class for binary elementwise operations"""

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.args = maybe_broadcast_elementwise(*self.args)
        if self.requires_grad:
            self.parents = self.args


class UnaryElementwiseOp(BaseOp):
    """Base class for unary elementwise operations"""

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        if self.requires_grad:
            self.parents = self.args

# %% ../../nbs/02_ops.common.ipynb 8
class Load(BaseOp):
    """Load a tensor"""

    name_template = "?"

    def __init__(self, name=None):
        super().__init__(name=name)

# %% ../../nbs/02_ops.common.ipynb 9
class Add(BinaryElementwiseOp):
    """Add two tensors"""

    name_template = "({}+{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.set_out(self.args[0].data + self.args[1].data)

    # def __call__(self, a, b):
    #     return Add(a, b, name=self.name)

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(self.out.grad)
        self.parents[1].accum_grad(self.out.grad)

# %% ../../nbs/02_ops.common.ipynb 10
class Sub(BinaryElementwiseOp):
    """Subtract two tensors"""

    name_template = "({}-{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.set_out(self.args[0].data - self.args[1].data)

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(self.out.grad)
        self.parents[1].accum_grad(-self.out.grad)

# %% ../../nbs/02_ops.common.ipynb 11
class Mul(BinaryElementwiseOp):
    """Multiply two tensors"""

    name_template = "({}*{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.set_out(self.args[0].data * self.args[1].data)

    def backward(self):
        self.check_backward()

        self.parents[0].accum_grad(self.out.grad * self.parents[1].data)
        self.parents[1].accum_grad(self.out.grad * self.parents[0].data)

# %% ../../nbs/02_ops.common.ipynb 12
class Div(BinaryElementwiseOp):
    """Divide two tensors"""

    name_template = "({}/{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.set_out(self.args[0].data / self.args[1].data)

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(self.out.grad / self.parents[1].data)
        self.parents[1].accum_grad(
            -self.out.grad * self.parents[0].data / (self.parents[1].data ** 2)
        )

# %% ../../nbs/02_ops.common.ipynb 13
class Neg(UnaryElementwiseOp):
    """Negate a tensor"""

    name_template = "(-{})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        self.set_out(-self.args[0].data)

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(-self.out.grad)

# %% ../../nbs/02_ops.common.ipynb 14
class Pow(UnaryElementwiseOp):
    """Raise a tensor to a power"""

    def __init__(self, a, power, name=None):
        self.name_template = f"pow({{}},{power})"
        super().__init__(a, name=name)
        self.power = power
        self.set_out(self.args[0].data ** power)

    def backward(self):
        self.check_backward()
        with np.errstate(divide="ignore"):
            self.parents[0].accum_grad(
                (self.out.grad * self.power * self.parents[0].data ** (self.power - 1))
            )

# %% ../../nbs/02_ops.common.ipynb 15
class Log(UnaryElementwiseOp):
    """Take the natural logarithm of a tensor"""

    name_template = "log({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        self.set_out(np.log(self.args[0].data))

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(self.out.grad / self.parents[0].data)

# %% ../../nbs/02_ops.common.ipynb 16
class Exp(UnaryElementwiseOp):
    """Exponentiate a tensor"""

    name_template = "exp({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        self.set_out(np.exp(self.args[0].data))

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(self.out.grad * self.out.data)

# %% ../../nbs/02_ops.common.ipynb 17
class ExpLog(UnaryElementwiseOp):
    """Exponentiate a tensor"""

    name_template = "exp({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)

        def logexp(x):
            return np.where(x < 0, np.log(1 + np.exp(x)), x + np.log(1 + np.exp(-x)))

        self.set_out(logexp(self.args[0].data))

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(
            self.out.grad * (1 - 1 / (1 + np.exp(self.parents[0].data)))
        )

# %% ../../nbs/02_ops.common.ipynb 18
class Matmul(BaseOp):
    """Matrix multiplication of two tensors"""

    name_template = "({}@{})"

    def __init__(self, a, b, name=None):
        super().__init__(a, b, name=name)
        self.args = maybe_broadcast_matmul(*self.args)
        if self.requires_grad:
            self.parents = self.args

        self.set_out(np.matmul(self.args[0].data, self.args[1].data))

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(
            np.matmul(self.out.grad, self.parents[1].data.swapaxes(-1, -2))
        )
        self.parents[1].accum_grad(
            np.matmul(self.parents[0].data.swapaxes(-1, -2), self.out.grad)
        )

# %% ../../nbs/02_ops.common.ipynb 19
class Sum(BaseOp):
    """Sum-reduce a tensor along the given axis (int or tuple of ints)"""

    name_template = "sum({})"

    def __init__(
        self,
        a,
        axis=None,
        keepdims=False,
        name=None,
    ):
        super().__init__(a, name=name)
        self.parents = self.args if self.requires_grad else []
        self.set_out(np.sum(self.args[0].data, axis=axis, keepdims=keepdims))

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(self.out.grad)  # This will broadcast correctly

# %% ../../nbs/02_ops.common.ipynb 20
class Broadcast(BaseOp):
    """Broadcast a tensor to the given shape"""

    name_template = "broadcast({})"

    def __init__(self, a, target_shape, name=None):
        super().__init__(a, name=name)
        self.target_shape = target_shape
        self.parents = self.args if self.requires_grad else []
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

        self.set_out(data)

    def backward(self):
        self.check_backward()
        axis = tuple([i for i, dim in enumerate(self.broadcasted_dims) if dim])
        summed = self.out.grad.sum(axis=axis, keepdims=True)

        if summed.shape != self.parents[0].data.shape:
            summed = summed.reshape(self.parents[0].data.shape)

        self.parents[0].accum_grad(summed)

# %% ../../nbs/02_ops.common.ipynb 21
class Slice(UnaryElementwiseOp):
    name_template = "slice({})"

    def __init__(self, a, key, name=None):
        super().__init__(a, name=name)
        self.key = key
        self.set_out(self.args[0].data[key])

    def backward(self):
        self.check_backward()
        p = self.parents[0]

        if not p.requires_grad:
            return

        if p.grad is None:
            p.grad = np.zeros_like(p.data)

        p.grad[self.key] += self.out.grad

# %% ../../nbs/02_ops.common.ipynb 23
class Transpose(UnaryElementwiseOp):
    """Transpose a tensor"""

    name_template = "transpose({})"

    def __init__(self, a, dim0, dim1, name=None):
        super().__init__(a, name=name)
        self.dim0 = dim0
        self.dim1 = dim1
        self.set_out(np.swapaxes(self.args[0].data, dim0, dim1))

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(np.swapaxes(self.out.grad, self.dim0, self.dim1))

# %% ../../nbs/02_ops.common.ipynb 24
class Dropout(UnaryElementwiseOp):
    """Apply Dropout to a tensor"""

    name_template = "dropout({})"

    def __init__(self, a, p_drop=0.1, training=True, name=None):
        if p_drop == 0:
            return a

        super().__init__(a, name=name)
        assert 0 < p_drop < 1, f"p_drop must in (0, 1), got {p_drop}"
        self.p_drop = p_drop
        self.training = training
        if training:
            # Note: We scale up the outputs during training rather than scaling down during inference.
            scale_factor = 1 / (1 - p_drop)
            self.mask = np.random.binomial(
                scale_factor, 1 - p_drop, size=self.args[0].data.shape
            )
            self.set_out(self.args[0].data * self.mask)
        else:
            self.set_out(self.args[0].data)

    def backward(self):
        self.check_backward()
        self.parents[0].accum_grad(self.out.grad * (self.mask if self.training else 1))

# %% ../../nbs/02_ops.common.ipynb 25
class Embedding(UnaryElementwiseOp):
    """Embedding layer"""

    name_template = "embedding({})"

    def __init__(self, a, indices, name=None):
        super().__init__(a, name=name)
        self.indices = indices
        self.set_out(self.args[0].data[self.indices])

    def backward(self):
        self.check_backward()
        if self.parents[0].grad is None:
            self.parents[0].grad = np.zeros_like(self.parents[0].data, dtype=np.float32)
        self.parents[0].grad[self.indices] += self.out.grad