"""Base classes for benchmarking metrics."""

from abc import ABC, abstractmethod

from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame


@define
class Metric(ABC):
    """Abstract base class for all benchmarking metrics."""

    doe_iteration_header: str = field(default="Iterations", validator=instance_of(str))
    """The name of the column in the DataFrame that
    contains the number of iterations."""

    to_evaluate_row_header: str = field(validator=instance_of(str))
    """The name of the column in the DataFrame that
    contains the values to evaluate."""

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

