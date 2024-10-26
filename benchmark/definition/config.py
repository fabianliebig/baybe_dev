"""Configuration for benchmarking."""

from typing import Any

from attrs import define, field
from attrs.validators import instance_of

from baybe.recommenders.base import RecommenderProtocol


@define(frozen=True)
class BenchmarkScenarioConfig:
    """Configuration for benchmarking."""

    batch_size: int = field(validator=instance_of(int))
    """The batch size for the benchmark."""

    n_doe_iterations: int = field(validator=instance_of(int))
    """The number of design of experiment iterations."""

    n_mc_iterations: int = field(validator=instance_of(int))
    """The number of Monte Carlo iterations."""

    recommender: list[RecommenderProtocol] = field()
    """The recommender to use for the benchmark.
    For each recommender, a campaign will be created."""

    @recommender.validator
    def _check_recommender(self, _: Any, value: list[RecommenderProtocol]):
        """Check if the recommender is a list of RecommenderProtocol."""
        if not value:
            raise ValueError("At least one recommender must be provided.")
        if not isinstance(value, list):
            raise ValueError("Recommender must be a list.")
        if not all(
            isinstance(recommender, RecommenderProtocol) for recommender in value
        ):
            raise ValueError("All recommenders must be of type RecommenderProtocol.")
