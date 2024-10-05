"""End-to-end tests for the performance of the BayBE package.

Tests the performance of the BayBE package by executing long running and compute
intensive example scenarios and persisting the results so that they can be
compared between different versions of the package.
"""

import os
from collections.abc import Sequence
from datetime import datetime

import pytest
from filelock import FileLock
from pytest import TempPathFactory

from tests.performance_tests.test_cases import (
    SCENARIO_TEST_CASES,
    SIMULATE_EXPERIMENT_TEST_CASES,
    TRANSFER_LEARNING_TEST_CASES,
)
from tests.performance_tests.utils import (
    LocalExperimentResultPersistence,
    PerformanceTestCase,
    ResultPersistenceInterface,
    S3ExperimentResultPersistence,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("BAYBE_TEST_ENV") != "PERFORMANCETEST",
    reason="Only possible in PERFORMANCETEST environment.",
)


def all_test_cases_uniquely_identifiable(
    test_case_list: Sequence[PerformanceTestCase],
) -> bool:
    """Check if all test cases in the list have unique identifiers.

    Args:
        test_case_list: A list of performance test cases.

    Returns:
        bool: True if all test cases have unique identifiers, False otherwise.
    """
    unique_uuids = {testcase.unique_id for testcase in test_case_list}
    return len(test_case_list) == len(unique_uuids)


def combine_simulations() -> Sequence[PerformanceTestCase]:
    """Combines multiple lists of performance test cases into a single sequence.

    This function merges the test cases from SCENARIO_TEST_CASES,
    SIMULATE_EXPERIMENT_TEST_CASES, and TRANSFER_LEARNING_TEST_CASES into
    one list. It ensures that all test cases have unique identifiers to
    facilitate comparison of their results over time.

    Returns:
        Sequence[PerformanceTestCase]: A combined list of performance test cases.

    Raises:
        ValueError: If any of the test cases do not have unique identifiers.
    """
    testcase_list: Sequence[PerformanceTestCase] = (
        SCENARIO_TEST_CASES
        + SIMULATE_EXPERIMENT_TEST_CASES
        + TRANSFER_LEARNING_TEST_CASES
    )
    if not all_test_cases_uniquely_identifiable(testcase_list):
        raise ValueError(
            "All performance test cases must have unique "
            "names to compare their results over time."
        )
    return testcase_list


@pytest.fixture(scope="session")
def time_stamp_test_execution(
    tmp_path_factory: TempPathFactory, worker_id: str
) -> datetime:
    """This function returns the timestamp of test execution.

    This function is used to ensure that the tests are running in parallel while using
    the same timestamp for all tests. Since the worker execute just a different subset
    of the tests which are parallelized but do run the fixture function independently,
    the date is stored in a file and read from there. For more information see:
    https://pytest-xdist.readthedocs.io/en/stable/how-to.html#making-session-scoped-fixtures-execute-only-once
    Since the date becomes part of the key for persisting the results,
    it is important that all tests use the same date.

    Args:
        tmp_path_factory: The factory for temporary directories.
        worker_id: The ID of the worker.

    Returns:
        datetime: The timestamp of the test execution.
    """
    NOT_RUNNING_IN_PARALLEL = worker_id == "master"
    if NOT_RUNNING_IN_PARALLEL:
        return datetime.now()

    root_tmp_dir = tmp_path_factory.getbasetemp().parent

    fn = root_tmp_dir / "date.txt"
    with FileLock(str(fn) + ".lock"):
        if not fn.is_file():
            date = datetime.now()
            fn.write_text(date.isoformat())
            return date

        saved_date: str = fn.read_text()
        return datetime.fromisoformat(saved_date)


@pytest.fixture(scope="function")
def result_data_handler(
    time_stamp_test_execution: datetime,
) -> ResultPersistenceInterface:
    """Returns an instance of ResultPersistenceInterface for storing experiment results.

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


@pytest.mark.parametrize("scenario", combine_simulations())
def test_performance_test(
    scenario: PerformanceTestCase, result_data_handler: ResultPersistenceInterface
) -> None:
    """Run the performance test for the given scenario."""
    simulation_results = scenario.execute_testcase()
    result_data_handler.persist_new_result(scenario.unique_id, simulation_results)
    assert False  # This is a placeholder for the actual test
