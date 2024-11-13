"""Executes the benchmarking module."""
# Run this via 'python -m benchmarks' from the root directory.

from benchmarks.domains import BENCHMARKS
from benchmarks.persistance import S3ExperimentResultPersistence


def main():
    """Run all benchmarks."""
    persistance_handler = S3ExperimentResultPersistence()

    for benchmark in BENCHMARKS:
        result = benchmark()
        persistance_handler.persist_new_result(result, benchmark)


if __name__ == "__main__":
    main()
