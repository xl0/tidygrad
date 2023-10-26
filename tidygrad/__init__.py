__version__ = "0.0.1"

import numpy as np
from .utils import datasets, data

__all__ = [datasets, data]

np.seterr(under="ignore")
