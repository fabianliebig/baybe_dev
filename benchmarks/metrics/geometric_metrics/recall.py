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
        data_numeric = self._get_geometric_input_as_dataframe(data)

        number_of_good_results = 0
        for optimal_input in self.optimal_function_inputs:
            for _, row in data_numeric.iterrows():
                iter_best = row.to_dict()
                distance = 0
                for key, value in optimal_input.items():
                    distance += (value - iter_best[key]) ** 2

                if distance <= self.excepted_distance:
                    number_of_good_results += 1
                    break

        return number_of_good_results
