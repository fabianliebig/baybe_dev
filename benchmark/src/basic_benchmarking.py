"""A basic benchmarking class for testing."""

import time

from attrs import define, field

from benchmark.src.base import Benchmark
from benchmark.src.result.basic_results import SingleResult


@define
class SingleExecutionBenchmark(Benchmark):
    """A basic benchmarking class for testing a single benchmark execution."""

    _benchmark_result: SingleResult = field(default=None)
    """The result of the benchmarking which is set after execution."""

    def execute_benchmark(self) -> SingleResult:
        """Execute the benchmark.

        The function will execute the benchmark and return
        the result apply added metrics if any were set and
        measures execution time.
        """
        try:
            start_ns = time.perf_counter_ns()
            result, self._metadata = self.benchmark_function()
            stop_ns = time.perf_counter_ns()
        except Exception as e:
            raise Exception(f"Error in benchmark {self.identifier}: {e}")
        time_delta = stop_ns - start_ns
        self._benchmark_result = SingleResult(
            self.title, self.identifier, self._metadata, result, time_delta
        )
        for metric in self.metrics:
            self._benchmark_result.evaluate_result(metric, self.objective_scenarios)
        return self._benchmark_result

    def get_result(self) -> SingleResult:
        """Return the single result of the benchmark.

        Will run the benchmark if it has not been executed yet.
        """
        if not self._benchmark_result:
            self._benchmark_result = self.execute_benchmark()
        return self._benchmark_result
