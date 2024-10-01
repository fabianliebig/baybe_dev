"""End-to-end tests for the performance of the baybe package.

Tests the performance of the baybe package by executing long running and compute
intensive example scenarios and persisting the results so that they can be
compared between different versions of the package.
"""

import os
from datetime import datetime
from typing import Sequence

import pytest
from filelock import FileLock
from pytest import TempPathFactory

from tests.performance_tests.test_cases import (
    SCENARIO_TEST_CASES,
    SIMULATE_EXPERIMENT_TEST_CASES,
    TRANSFER_LEARNING_TEST_CASES,
)
from tests.performance_tests.utils import (
    ResultPersistenceInterface,
    S3ExperimentResultPersistence,
    TestCase,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("BAYBE_TEST_ENV") != "PERFORMANCETEST",
    reason="Only possible in PERFORMANCETEST environment.",
)


def all_test_cases_uniquely_identifiable(test_case_list: Sequence[TestCase]) -> bool:
    """Check if all test cases have unique names.

    Returns:
        bool: True if all test cases have unique names, False otherwise.
    """
    unique_uuids = set([testcase.unique_id for testcase in test_case_list])
    return len(test_case_list) == len(unique_uuids)


def combine_simulations() -> Sequence[TestCase]:
    """Combines different sets of test cases into a single list.

    Returns:
        List[TestCase]: A list containing all the test cases from SCENARIO_TEST_CASES,
        SIMULATE_EXPERIMENT_TEST_CASES, and TRANSFER_LEARNING_TEST_CASES.
    """
    testcase_list: Sequence[TestCase] = (
        SCENARIO_TEST_CASES
        + SIMULATE_EXPERIMENT_TEST_CASES
        + TRANSFER_LEARNING_TEST_CASES
    )
    if not all_test_cases_uniquely_identifiable(testcase_list):
        raise ValueError(
            "All test cases must have unique "
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
        tmp_path_factory (TempPathFactory): The factory for creating temporary directories.
        worker_id (str): The ID of the worker.

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

    Parameters:
        test_time_stamp (datetime): The timestamp of the test.

    Returns:
        ResultPersistenceInterface: An instance of ResultPersistenceInterface.

    """
    return S3ExperimentResultPersistence(time_stamp_test_execution)


@pytest.mark.parametrize("scenario", combine_simulations())
def test_performance_test(
    scenario: TestCase, result_data_handler: ResultPersistenceInterface
) -> None:
    """Run the performance test for the given scenario."""
    simulation_results = scenario.execute_testcase()
    result_data_handler.persist_new_result(scenario.unique_id, simulation_results)
    print(result_data_handler.load_compare_result(scenario.unique_id))
    assert False  # This is a placeholder for the actual test
