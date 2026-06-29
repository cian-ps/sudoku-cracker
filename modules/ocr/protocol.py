from __future__ import annotations

from typing import Any, Protocol

import numpy as np


class OCRBackend(Protocol):
    def predict(self, image: np.ndarray) -> list[dict[str, Any]]: ...
