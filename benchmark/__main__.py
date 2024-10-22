"""Run the benchmarks for the given scenario."""

import concurrent.futures
import os

from benchmark.domain import SINGE_BENCHMARKS_TO_RUN
from benchmark.src import (
    SingleResult,
)


def main():
    """Run the performance test for the given scenario.

    This function runs the performance test cases defined in the domain module
    in parallel. The function uses the number of cores available on the machine
    to create a reasonable number of workers for the execution.
    The results of the benchmarks are persisted to the file system or S3.
    """
    num_cores = os.cpu_count()
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = [
            executor.submit(func.execute_benchmark) for func in SINGE_BENCHMARKS_TO_RUN
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                result_benchmarking: SingleResult = future.result()
                print(f"Result: {result_benchmarking}")
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
