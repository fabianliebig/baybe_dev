"""Base classes for benchmarking metrics."""

import ast
from abc import ABC, abstractmethod
from typing import Any, Protocol

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame

from baybe.targets.enum import TargetMode
import numpy as np


@define
class Metric(Protocol):
    """Abstract base class for all benchmarking metrics."""

    def evaluate(self, data: DataFrame) -> float:
        """Evaluate the given data against the objective scenario.

        Args:
            data: The data to evaluate from the an benchmark result.
                It must contain the objective scenarios to evaluate only.

        Returns:
            float: The evaluation metric value.
        """


@define
class ValueMetric(Metric, ABC):
    """Abstract base class for all regret metrics."""

    doe_iteration_header: str = field(
        default="Iteration", validator=instance_of(str), kw_only=True
    )
    """The name of the column in the DataFrame that
    contains the number of iterations."""

    target_mode: TargetMode = field(validator=instance_of(TargetMode))
    """The objective to evaluate."""

    to_evaluate_row_header: str = field(validator=instance_of(str))
    """The name of the column in the DataFrame that
    contains the values to evaluate."""


@define
class BestValueMetric(ValueMetric, ABC):
    """Abstract base class for all regret metrics that require the best value."""

    value_range: tuple[float, float] | None = field()
    """The maximum value in the lookup table or function."""

    best_value: tuple[float, float] | None = field(init=False)
    """The best value to consider."""

    @best_value.default
    def _best_value_default(self):
        if self.value_range is None:
            return None

        return (
            self.value_range[1]
            if self.target_mode is TargetMode.MAX
            else self.value_range[0]
        )


@define
class GeometricMetric(Metric, ABC):
    """Abstract base class for all geometric metrics."""

    used_input_column_header: str = field(validator=instance_of(str))
    """The name of the column in the DataFrame that contains the input values
    of the objective function for the given iteration."""

    monte_carlo_iterations: int = field(validator=instance_of(int))
    """The number of monte carlo iterations to evaluate the metric.
    This will calculate the mean of the metric value."""

    objective_name: str = field(validator=instance_of(str))
    """The name of the objective to evaluate."""

    target_mode: TargetMode = field(validator=instance_of(TargetMode))
    """The objective to evaluate."""

    doe_iteration_header: str = field(
        default="Iteration", validator=instance_of(str), kw_only=True
    )
    """The name of the column in the DataFrame that
    contains the number of iterations."""

    categorical_parameter: dict[str, list[str]] = field(kw_only=True, default={})
    """The categorical parameter map to represent the categorical values as numeric.
    Only relevant if the input values are categorical. The kex is the input identifier
    and the value is the list of unique values for that input."""

    def _categorical_parameter_converter(
        input: dict[str, list[str]],
    ) -> dict[str, list[str]]:
        for key, value in input.items():
            value.sort()
            input[key] = value
        return input

    categorical_parameter: dict[str, list[str]] = field(
        kw_only=True, default={}, converter=_categorical_parameter_converter
    )

    def _parse_input_from_dataframe(self, input_values: str) -> dict[str, Any]:
        """Parse the input values from the DataFrame.

        Args:
            input_values: The input values from the DataFrame.

        Returns:
            float: The parsed input values.
        """
        json_input = ast.literal_eval(input_values)

        input_df = DataFrame.from_dict(json_input)
        target_index_best_iter = self._find_optimal_index(input_df)

        cat_value = {}

        opt_input = input_df.loc[target_index_best_iter]

        for key, value in opt_input.to_dict().items():
            if key in self.categorical_parameter:
                cat_value[key] = self.categorical_parameter[key].index(value)
                continue
            cat_value[key] = value

        return cat_value

    def _find_optimal_index(self, input_df):
        if self.target_mode is TargetMode.MAX:
            target_index_best_iter = input_df[self.objective_name].idxmax()
            return target_index_best_iter

        target_index_best_iter = input_df[self.objective_name].idxmin()
        return target_index_best_iter

    def _get_geometric_input_as_dataframe(self, data: DataFrame) -> DataFrame:
        """Get the input values as a DataFrame."""
        geo_series = data[self.used_input_column_header].apply(
            lambda x: self._parse_input_from_dataframe(x)
        )
        return DataFrame(geo_series.tolist())

    def _compute_squared_radius(self, data_numeric):
        """Compute the squared radius of the ball over the vector space."""
        data_array = data_numeric.to_numpy()
        centroid = np.median(data_array, axis=0)
        squared_distances = np.sum((data_array - centroid) ** 2, axis=1)
        return np.quantile(squared_distances, 0.25)

    @abstractmethod
    def _count_within_distance(self, data: DataFrame):
        """Represent the categorical values as numeric."""


@define
class BestInputGeometricMetric(GeometricMetric):
    """Abstract base class for all geometric metrics that require the best input."""

    reference_data: DataFrame = field(validator=instance_of(DataFrame))
    """Data to calculate the median distance between points.
    Will be used to calculate the number of good results."""

    excepted_distance: float = field(validator=instance_of(float), init=False)
    """The distance to consider two points as close.
    Will be used to calculate the number of good results."""

    @excepted_distance.default
    def _set_excepted_distance(self):
        data_numeric = self._get_geometric_input_as_dataframe(self.reference_data).drop(
            columns=[self.objective_name]
        )
        return self._compute_squared_radius(data_numeric)

    optimal_function_inputs: list[dict[str, Any]] = field()
    """An input that creates the best_possible_result."""

    def __attrs_post_init__(self):
        """Convert the categorical values to numeric."""
        for i in range(len(self.optimal_function_inputs)):
            for key, value in self.optimal_function_inputs[i].items():
                if isinstance(value, str):
                    self.optimal_function_inputs[i][key] = self.categorical_parameter[
                        key
                    ].index(value)
