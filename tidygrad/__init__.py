__version__ = "0.0.1"

import numpy as np
np.seterr(under="warn")
del np

from .utils import datasets, data
from .tensor import Tensor, no_grad
from .func import *

from . import model

# __all__ = [datasets, data, no_grad, Tensor]
