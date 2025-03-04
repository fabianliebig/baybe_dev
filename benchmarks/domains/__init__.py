"""Benchmark domains."""

from benchmarks.definition.base import Benchmark
from benchmarks.domains.synthetic_2C1D_1C import synthetic_2C1D_1C_benchmark

BENCHMARKS: dict[str, Benchmark] = {
    "synthetic_2C1D_1C": synthetic_2C1D_1C_benchmark,
}

__all__ = ["BENCHMARKS"]
