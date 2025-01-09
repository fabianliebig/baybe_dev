"""Average distance metric."""

import numpy as np
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
        training_data = self._get_geometric_input_as_dataframe(data)

        Y = training_data[self.objective_name]
        X = training_data.drop(columns=[self.objective_name])

        nn_classifier = KMeans(
            n_clusters=self.number_of_nearest_neighbors, random_state=42
        )
        predicted_classes = nn_classifier.fit_predict(X, Y)

        summed_distance = 0
        training_data_np = training_data.to_numpy()
        for i in range(len(training_data_np)):
            for j in range(i + 1, len(training_data_np)):
                if predicted_classes[i] != predicted_classes[j]:
                    continue

                distance = np.linalg.norm(training_data_np[i] - training_data_np[j])
                summed_distance += distance

        return summed_distance
