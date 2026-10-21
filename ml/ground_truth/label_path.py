
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ml.ground_truth.label_status import LabelStatus


@dataclass(frozen=True)
class LabeledPath:
    finding_id: str
    test_name: Optional[str]
    category: Optional[str]
    status: LabelStatus
 
    @property
    def label(self) -> Optional[int]:
        """1 / 0 для обучения; None: такой алерт в датасет брать нельзя."""
        if self.status is LabelStatus.TP:
            return 1
        if self.status is LabelStatus.FP:
            return 0
        return None
