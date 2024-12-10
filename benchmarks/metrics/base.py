"""Base classes for benchmarking metrics."""

from abc import ABC, abstractmethod
from typing import Protocol

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame


@define
class Metric(Protocol):
    """Abstract base class for all benchmarking metrics."""

    @abstractmethod
    def evaluate(self, data: DataFrame) -> float:
        """Evaluate the given datas against the objective scenario.

        Args:
            data: The datas to evaluate from the an benchmark result.
                It must contain the objective scenarios to evaluate only.

        Returns:
            float: The evaluation metric value.
        """
        pass


@define
class ValueMetric(Metric, ABC):
    """Abstract base class for all regret metrics."""

    doe_iteration_header: str = field(
        default="Iteration", validator=instance_of(str), kw_only=True
    )
    """The name of the column in the DataFrame that
    contains the number of iterations."""

    to_evaluate_row_header: str = field(validator=instance_of(str))
    """The name of the column in the DataFrame that
    contains the values to evaluate."""


@define
class GeometricMetric(Metric, ABC):
    """Abstract base class for all geometric metrics."""

    used_input_column_header: str = field(validator=instance_of(str))
    """The name of the column in the DataFrame that contains the input values
    of the objective function for the given iteration."""
    doe_iteration_header: str = field(
        default="Iteration", validator=instance_of(str), kw_only=True
    )
    """The name of the column in the DataFrame that
    contains the number of iterations."""
