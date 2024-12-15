"""Simple regret metric."""

import numpy as np
from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class SimpleRegret(ValueMetric):
    """Simple Regret metric."""

    best_value: float = field(validator=instance_of(float))
    """Best value to compare the result with."""

    objective: TargetMode = field(validator=instance_of(TargetMode))
    """The target mode to evaluate the objective."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the simple regret for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed AUC value.
        """
        if self.objective == TargetMode.MIN:
            min_found = data[self.to_evaluate_row_header].min()
            simple_regret = abs(self.best_value - min_found)
            return simple_regret

        max_found = data[self.to_evaluate_row_header].max()
        simple_regret = abs(self.best_value - max_found)
        return simple_regret


@define
class NormalizedSimpleRegret(SimpleRegret):
    """Normalized simple regret."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the normalized simple regret for a data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed normalized AUC value.
        """
        regret = super().evaluate(data)
        normalized_regret = regret / (self._max_value_y - self._min_value_y)
        return normalized_regret
