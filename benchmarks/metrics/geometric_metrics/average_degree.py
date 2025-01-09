"""Average degree metric."""

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from benchmarks.metrics.base import GeometricMetric


@define
class AverageDegree(GeometricMetric):
    """Show how many points are mutually close and eventually express exploitation."""

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
        data_numeric = self._get_geometric_input_as_dataframe(data).drop(
            columns=[self.objective_name]
        )

        number_of_good_results = 0
        for i, row_outer in data_numeric.iterrows():
            for j, row_inner in data_numeric.iterrows():
                if i == j:
                    continue
                distance = 0
                for key in row_outer.index:
                    distance += (row_inner[key] - row_outer[key]) ** 2

                if distance <= self.excepted_distance:
                    number_of_good_results += 1

        return number_of_good_results
