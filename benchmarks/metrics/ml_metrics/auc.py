"""Area Under the Curve (AUC) metric."""

import numpy as np
from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import ValueMetric


@define
class AreaUnderTheCurve(ValueMetric):
    """Area Under the Curve (AUC) metric."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the Area Under the Curve (AUC) for given.

        Args:
            data: containing the scenario to evaluate.

        Returns:
            float: The computed AUC value.
        """
        data = data.copy(True)
        header = self.to_evaluate_row_header
        data = data.groupby(self.doe_iteration_header)[header].mean().reset_index()

        if self.target_mode == TargetMode.MIN:
            data[header] -= data[header].max()
        elif self.target_mode == TargetMode.MAX:
            data[header] -= data[header].min()

        x = data[self.doe_iteration_header].values
        y = data[header].values

        auc = np.trapz(y, x)
        return abs(auc)


@define
class NormalizedAreaUnderTheCurve(AreaUnderTheCurve):
    """Normalize the Area Under the Curve (AUC) metric."""

    lookup: DataFrame | tuple[float, float]
    """The lookup table or function to evaluate the goal orientation
    metric and compare the best included result."""

    _max_value_y: float = field(init=False, validator=instance_of(float))
    """The maximum value in the lookup table or function."""

    _min_value_y: float = field(init=False, validator=instance_of(float))
    """The minimum value in the lookup table or function."""

    def _normalize_data(self, data: DataFrame, index_name: str) -> DataFrame:
        """Normalize the specified column in the DataFrame using min-max normalization.

        Args:
            data: The input DataFrame containing the data to be normalized.
            index_name: The name of the column to be normalized. Usually
                        the objective name.

        Returns:
            DataFrame: The DataFrame with the specified column normalized.
        """
        data = data.copy(True)
        data[index_name] = data[index_name].apply(
            lambda x: (x - self._min_value_y) / (self._max_value_y - self._min_value_y)
        )
        return data

    @_max_value_y.default
    def _max_value_y_default(self) -> float:
        """Set the default value for the max value."""
        if isinstance(self.lookup, tuple):
            _, max = self.lookup
            return max
        return self.lookup[self.objective_name].max()

    @_min_value_y.default
    def _max_value_y_default(self) -> float:
        """Set the default value for the min value."""
        if isinstance(self.lookup, tuple):
            min, _ = self.lookup
            return min
        return self.lookup[self.objective_name].min()

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the normalized Area Under the Curve (AUC) for given data.

        Args:
            data: Containing the scenario to evaluate.

        Returns:
            float: The computed normalized AUC value.
        """
        iterations = data[self.doe_iteration_header].unique().size
        normalization_factor = (self._max_value_y - self._min_value_y) * iterations

        return super().evaluate(data) / normalization_factor
