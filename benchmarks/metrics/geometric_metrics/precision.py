"""Copulative regret."""

import ast
import math
from typing import Any

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from baybe.targets.enum import TargetMode
from benchmarks.metrics.base import GeometricMetric


@define
class Precision(GeometricMetric):
    """Simple Regret metric."""

    lookup: DataFrame | tuple[float, float] = field(
        validator=instance_of((DataFrame, tuple))
    )
    """The lookup table or function to evaluate the goal orientation
    metric and compare the best included result."""

    radius_for_optimal_input: float = field(validator=instance_of(float))
    """The radius to consider based on some optimal input x.
    All the inputs that are within this radius are considered "good"."""

    objective_name: str = field(validator=instance_of(str))
    """The name of the objective to evaluate."""

    target_mode: TargetMode = field(validator=instance_of(TargetMode))
    """The objective to evaluate."""

    optimal_function_inputs: list[dict[str, Any]] = field()
    """An input that creates the best_possible_result."""

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

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the the regret of finding the optimal solutions.

        Args:
            data: data data containing the scenario to evaluate.

        Returns:
            float: The computed AUC value.
        """
        excepted_distance = self.radius_for_optimal_input**2
        cathegorical_parameter_map = {}
        example_input = self.optimal_function_inputs[0]
        for key, value in example_input.items():
            if isinstance(value, str):
                unique_values = data[key].unique()
                cathegorical_parameter_map[key] = {
                    value: i for i, value in enumerate(unique_values)
                }

        number_of_good_results = 0
        for _, row in data.iterrows():
            input_values = row[self.used_input_column_header]
            iter_best = self._parse_input_from_dataframe(input_values)
            for optimal_input in self.optimal_function_inputs:
                distance = 0
                for key, value in optimal_input.items():
                    if key in cathegorical_parameter_map:
                        distance += (
                            cathegorical_parameter_map[key][value]
                            - cathegorical_parameter_map[key][iter_best[key]]
                        ) ** 2
                        continue
                    distance += (value - iter_best[key]) ** 2
                if math.sqrt(distance) <= excepted_distance:
                    number_of_good_results += 1

        return excepted_distance / data[self.doe_iteration_header].unique().size
