"""Basic result classes for benchmarking."""

from attrs import define
from pandas import DataFrame
from typing_extensions import override

from benchmark.src.result.base import Result


@define(frozen=True)
class SingleResult(Result):
    """A single result of the benchmarking."""

    benchmark_result: DataFrame
    """The result of the benchmarking."""

    execution_time_ns: int
    """The execution time of the benchmark in nanoseconds."""

    @override
    def get_execution_time_ns(self) -> float:
        """Return the execution time of the benchmark in nanoseconds."""
        return self.execution_time_ns
