__version__ = "0.0.1"

import numpy as np
np.seterr(under="ignore")
del np

from .utils import datasets, data
from .tensor import Tensor, no_grad
from .func import *

# __all__ = [datasets, data, no_grad, Tensor]
