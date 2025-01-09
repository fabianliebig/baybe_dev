"""Simple regret metric."""

from attrs import define
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import BestValueMetric


@define
class SimpleRegret(BestValueMetric):
    """Simple Regret metric."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the simple regret for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed AUC value.
        """
        if self.target_mode == TargetMode.MIN:
            min_found = data.groupby(self.doe_iteration_header)[
                self.to_evaluate_row_header
            ].mean().min()
            simple_regret = abs(self.best_value - min_found)
            return simple_regret

        max_found = data.groupby(self.doe_iteration_header)[
            self.to_evaluate_row_header
        ].mean().max()
        simple_regret = abs(max_found - self.best_value)
        return simple_regret
