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
        data_numeric = self._get_geometric_input_as_dataframe(data)

        number_of_good_results = 0
        for _, row in data_numeric.iterrows():
            iter_best = row.to_dict()
            for optimal_input in self.optimal_function_inputs:
                distance = 0
                for key, value in optimal_input.items():
                    distance += (iter_best[key] - value) ** 2

                if distance <= self.excepted_distance:
                    number_of_good_results += 1
                    break

        return number_of_good_results
