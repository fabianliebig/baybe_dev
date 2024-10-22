"""Base class for benchmarking implementations."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from uuid import UUID, uuid4

from attrs import define, field
from pandas import DataFrame
from typing_extensions import override

from benchmark.src.metric import Metric
from benchmark.src.result import Result


@define
class Benchmark(ABC):
    """Abstract base class for all benchmarks."""

    title: str
    """The title of the benchmark."""

    benchmark_function: Callable[[], tuple[DataFrame, dict[str, str]]]
    """The function that executes the benchmark code and returns
    the results as well as metadata."""

    objective_scenarios: list[str] = field(factory=lambda: list())
    """The name of the simulated scenarios referring to
    :func:`baybe.simulation.core.simulate_experiment`: to
    evaluate the benchmarking results."""

    identifier: UUID = field(factory=uuid4)
    """The unique identifier of the benchmark running which can be set
    to compare different executions of the same benchmark setting."""

    _metadata: dict[str, str] = field(factory=lambda: dict())
    """Metadata about the benchmark. Will be set after the benchmark is executed."""

    metrics: list[Metric] = field(factory=lambda: list())
    """Optional metrics to evaluate the benchmarking results."""

    @override
    def __str__(self) -> str:
        """Return a string representation of the object.

        Returns:
            str: The title of the object.
        """
        return self.title

    @override
    def __repr__(self) -> str:
        """Return a string representation of the object for debugging.

        Returns:
            str: A string that includes the class name,
            title, and identifier of the object.
        """
        classname = self.__class__.__name__
        return f"{classname}(name={self.title}, identifier={self.identifier})"

    @abstractmethod
    def execute_benchmark(self) -> Result:
        """Execute the benchmark and return the results."""
        pass

    @abstractmethod
    def get_result(self) -> Result:
        """Return the results of the benchmark.

        Will run the benchmark if it has not been executed yet.
        """
        pass
