"""Recall metric."""

from attrs import define
from pandas import DataFrame
from typing_extensions import override

from benchmarks.metrics.base import BestInputGeometricMetric


@define
class Recall(BestInputGeometricMetric):
    """Recall as the count of global optima in the vicinity of query points."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate if all the optimal solutions where found.

        Args:
            data: data containing the scenario to evaluate.

        Returns:
            float: The computed recall value.
        """
        number_of_good_results = self._count_within_distance(data)

        return number_of_good_results / len(self.optimal_function_inputs)

    @override
    def _count_within_distance(self, data: DataFrame):
        """Count the number of good results within the distance."""
        excepted_distance = self.radius_for_optimal_input**2
        categorical_parameter_map = self._represent_categorical_as_numeric(data)

        number_of_good_results = 0
        for optimal_input in self.optimal_function_inputs:
            for _, row in data.iterrows():
                input_values = row[self.used_input_column_header]
                iter_best = self._parse_input_from_dataframe(input_values)
                distance = 0
                for key, value in optimal_input.items():
                    if key in categorical_parameter_map:
                        distance += (
                            categorical_parameter_map[key][value]
                            - categorical_parameter_map[key][iter_best[key]]
                        ) ** 2
                        continue
                    distance += (value - iter_best[key]) ** 2

                if distance <= excepted_distance:
                    number_of_good_results += 1
                    break

        return number_of_good_results
