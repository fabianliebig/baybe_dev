"""Average distance metric."""

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame
from sklearn.cluster import KMeans
from typing_extensions import override

from benchmarks.metrics.base import GeometricMetric


@define
class AverageDistance(GeometricMetric):
    """Indicated the degree of exploration by measuring the distance for k cluster."""

    number_of_nearest_neighbors: int = field(validator=instance_of(int))
    """The number of nearest neighbors to consider."""

    @override
    def evaluate(self, data: DataFrame) -> float:
        """Calculate the average distance in k cluster.

        Args:
            data: data containing the scenario to evaluate.

        Returns:
            float: The computed precision value.
        """
        number_of_good_results = self._count_within_distance(data)

        nearby_points_count = number_of_good_results / (
            data[self.doe_iteration_header].unique().size
            * self.number_of_nearest_neighbors
        )

        return (nearby_points_count) / self.monte_carlo_iterations

    @override
    def _count_within_distance(self, data: DataFrame):
        """Sum the distance between k cluster."""
        categorical_parameter_map = self._represent_categorical_as_numeric(data)

        training_data = {}
        for _, row in data.iterrows():
            input_values = row[self.used_input_column_header]
            iter_best_outer = self._parse_input_from_dataframe(input_values)
            for key, value in iter_best_outer.items():
                if key not in training_data:
                    training_data[key] = []
                training_data[key].append(value)

        training_data = DataFrame.from_dict(training_data)
        training_data = training_data.drop(columns=[self.objective_name])

        nn_classifier = KMeans(n_clusters=self.number_of_nearest_neighbors)
        nn_classifier.fit(training_data)

        predicted_classes = nn_classifier.predict(training_data)

        summed_distance = 0
        for i, row_outer in enumerate(training_data.itertuples(index=False)):
            for j, row_inner in enumerate(training_data.itertuples(index=False)):
                if predicted_classes[i] != predicted_classes[j]:
                    continue

                iter_best_outer = row_outer._asdict()
                iter_best_inner = row_inner._asdict()
                distance = 0
                for key, value in iter_best_inner.items():
                    if key in categorical_parameter_map:
                        distance += (
                            categorical_parameter_map[key][iter_best_outer[key]]
                            - categorical_parameter_map[key][value]
                        ) ** 2
                    else:
                        distance += (iter_best_outer[key] - value) ** 2

                summed_distance += distance**0.5

        return summed_distance
