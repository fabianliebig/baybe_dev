"""Average degree metric."""

from turtle import pd
from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from typing_extensions import override

from benchmarks.metrics.base import GeometricMetric


@define
class AverageDegree(GeometricMetric):
    """Show how many points are mutually close and eventually express exploitation."""

    radius_for_optimal_input: float = field(validator=instance_of(float))
    """The radius to consider based on some optimal input x.
    All the inputs that are within this radius are considered "good"."""

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

        data_numeric = data[self.used_input_column_header].apply(
            lambda x: self._parse_input_from_dataframe(x)
        )

        for key in categorical_parameter_map:
            data_numeric[key] = data_numeric[key].map(categorical_parameter_map[key])

        number_of_good_results = 0
        for row_outer in data_numeric:
            for row_inner in data_numeric:
                distance = 0
                for key, value in row_outer.items():
                    distance += (row_inner[key] - value) ** 2

                if distance <= excepted_distance:
                    number_of_good_results += 1

        return number_of_good_results - 1
