"""End-to-end tests for the performance of the BayBE package.

Tests the performance of the BayBE package by executing long running and compute
intensive example scenarios and persisting the results so that they can be
compared between different versions of the package.
"""

import concurrent.futures
import os
import time
from collections.abc import Sequence
from datetime import datetime

from performance_tests.test_cases import PERFORMANCE_TEST_CALLABLES, CallableType
from performance_tests.utils import (
    BenchmarkingResult,
    LocalExperimentResultPersistence,
    ResultPersistenceInterface,
    S3ExperimentResultPersistence,
)


def execute_test_case(
    test_case: CallableType,
) -> BenchmarkingResult:
    """Execute a performance test case and return the result."""
    start_ns = time.perf_counter_ns()
    result, unique_id, metadata = test_case()
    stop_ns = time.perf_counter_ns()
    execution_time = stop_ns - start_ns
    return BenchmarkingResult(result, unique_id, execution_time, metadata)


def result_data_handler(
    time_stamp_test_execution: datetime,
) -> ResultPersistenceInterface:
    """Create a result data handler.

    This fixture is used to store the results of the performance tests in a persistent
    way with a function scope to ensure that all test cases can run independently
    since basic boto3 is not thread safe but creating a boto3 client session is.
    For local testing, the results are stored in a local directory.

    Parameters:
        time_stamp_test_execution: The timestamp of the test.

    Returns:
        ResultPersistenceInterface: An instance of ResultPersistenceInterface.

    """
    if os.environ.get("BAYBE_PERFORMANCE_PERSISTANCE_PATH"):
        return S3ExperimentResultPersistence(time_stamp_test_execution)
    return LocalExperimentResultPersistence(time_stamp_test_execution)


def thread_test_cases(test_cases: Sequence[CallableType]) -> None:
    """Run the performance test for the given scenario."""
    num_cores = os.cpu_count()
    persistance_handler = result_data_handler(datetime.now())
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = [executor.submit(execute_test_case, func) for func in test_cases]
        for future in concurrent.futures.as_completed(futures):
            result_benchmarking = future.result()
            persistance_handler.persist_new_result(result_benchmarking)


if __name__ == "__main__":
    thread_test_cases(PERFORMANCE_TEST_CALLABLES)
