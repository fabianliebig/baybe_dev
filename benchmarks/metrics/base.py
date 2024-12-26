"""Base classes for benchmarking metrics."""

import ast
from abc import ABC, abstractmethod
from typing import Any, Protocol

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame

from baybe.targets.enum import TargetMode


@define
class Metric(Protocol):
    """Abstract base class for all benchmarking metrics."""

    def evaluate(self, data: DataFrame) -> float:
        """Evaluate the given datas against the objective scenario.

        Args:
            data: The datas to evaluate from the an benchmark result.
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

    best_value: float | None = field()
    """The best value to consider."""


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

    def _parse_input_from_dataframe(self, input_values: str) -> dict[str, Any]:
        """Parse the input values from the DataFrame.

        Args:
            input_values: The input values from the DataFrame.

        Returns:
            float: The parsed input values.
        """
        json_input = ast.literal_eval(input_values)
        input_df = DataFrame.from_dict(json_input)
        if self.target_mode is TargetMode.MAX:
            target_index_best_iter = input_df[self.objective_name].idxmax()
            return input_df.loc[target_index_best_iter]

        target_index_best_iter = input_df[self.objective_name].idxmin()
        return input_df.loc[target_index_best_iter].to_dict()

    def _represent_categorical_as_numeric(self, data: DataFrame):
        """Represent the categorical values as numeric."""
        categorical_parameter_map = {}
        example_input = self._parse_input_from_dataframe(
            data.iloc[0][self.used_input_column_header]
        )
        for key, value in example_input.items():
            if isinstance(value, str):
                unique_values = data[key].unique()
                categorical_parameter_map[key] = {
                    value: i for i, value in enumerate(unique_values)
                }

        return categorical_parameter_map

    @abstractmethod
    def _count_within_distance(self, data: DataFrame):
        """Represent the categorical values as numeric."""


@define
class BestInputGeometricMetric(GeometricMetric):
    """Abstract base class for all geometric metrics that require the best input."""

    optimal_function_inputs: list[dict[str, Any]] = field()
    """An input that creates the best_possible_result."""

    radius_for_optimal_input: float = field(validator=instance_of(float))
    """The radius to consider based on some optimal input x.
    All the inputs that are within this radius are considered "good"."""
