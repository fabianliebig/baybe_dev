"""Precision metric."""

from attrs import define
from pandas import DataFrame
from typing_extensions import override

from benchmarks.metrics.base import BestInputGeometricMetric


@define
class Precision(BestInputGeometricMetric):
    """Precision as the count the number of points in the vicinity of global optima."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate how many points are near at least one optimal solution.

        Args:
            data: data containing the scenario to evaluate.

        Returns:
            float: The computed precision value.
        """
        number_of_good_results = self._count_within_distance(data)

        return (
            number_of_good_results / data[self.doe_iteration_header].unique().size
        ) / self.monte_carlo_iterations

    @override
    def _count_within_distance(self, data: DataFrame):
        """Count the number of good results within the distance."""
        excepted_distance = self.radius_for_optimal_input**2
        categorical_parameter_map = self._represent_categorical_as_numeric(data)

        number_of_good_results = 0
        for _, row in data.iterrows():
            input_values = row[self.used_input_column_header]
            iter_best = self._parse_input_from_dataframe(input_values)
            for optimal_input in self.optimal_function_inputs:
                distance = 0
                for key, value in optimal_input.items():
                    if key in categorical_parameter_map:
                        distance += (
                            categorical_parameter_map[key][iter_best[key]]
                            - categorical_parameter_map[key][value]
                        ) ** 2
                        continue
                    distance += (iter_best[key] - value) ** 2

                if distance <= excepted_distance:
                    number_of_good_results += 1
                    break
        return number_of_good_results