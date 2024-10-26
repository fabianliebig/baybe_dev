"""This module contains the benchmarks for the different domains of the benchmark."""

from benchmark.definition.benchmarking import Benchmark
from benchmark.function_data.synthetic_3 import benchmark_synthetic_3

BENCHMARKS: list[Benchmark] = [
    benchmark_synthetic_3,
]

__all__ = ["BENCHMARKS"]
