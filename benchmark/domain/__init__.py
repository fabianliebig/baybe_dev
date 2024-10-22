"""This module contains the benchmarks for the different domains of the benchmark."""

from benchmark.domain.synthetic_3 import benchmark_synthetic_3
from benchmark.src import SingleExecutionBenchmark

SINGE_BENCHMARKS_TO_RUN: list[SingleExecutionBenchmark] = [
    benchmark_synthetic_3,
]

__all__ = ["SINGE_BENCHMARKS_TO_RUN"]
