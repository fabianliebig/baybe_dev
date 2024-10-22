"""Benchmarking module for executing and comparing performance related tasks."""

from benchmark.src.base import Benchmark
from benchmark.src.basic_benchmarking import (
    SingleExecutionBenchmark,
)
from benchmark.src.result import Result
from benchmark.src.result.basic_results import SingleResult

__all__ = [
    "Benchmark",
    "SingleExecutionBenchmark",
    "Result",
    "SingleResult",
]
