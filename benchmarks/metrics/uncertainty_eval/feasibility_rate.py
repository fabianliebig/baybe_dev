"""Feasibility rate metric for uncertainty evaluation."""

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import BestValueMetric


@define
class FeasibilityRate(BestValueMetric):
    """Count the number of converging iterations."""

    best_value: float = field(validator=instance_of(float))
    """Best value to compare the result with."""

    converge_area_percentage: float = field(validator=instance_of(float))
    """The percentage of the area to consider as the convergence area.
    all the values within this area will be considered as converged."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the feasible rate for given data.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed feasible rate value.
        """
        feasible_count = 0
        grouped_data = data.groupby(self.doe_iteration_header)
        for _, group in grouped_data:
            if self.target_mode == TargetMode.MIN:
                if group[self.to_evaluate_row_header].min() <= (
                    self.best_value * self.converge_area_percentage
                ):
                    feasible_count += 1
            if self.target_mode == TargetMode.MAX:
                if group[self.to_evaluate_row_header].max() >= (
                    self.best_value * self.converge_area_percentage
                ):
                    feasible_count += 1

        return feasible_count / len(grouped_data)
