"""End-to-end tests for the performance of the baybe package.

Tests the performance of the baybe package by executing long running and compute
intensive example scenarios and persisting the results so that they can be
compared between different versions of the package.
"""

import os
from datetime import datetime
from typing import Sequence

import pytest

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
def test_time_stamp() -> datetime:
    """Returns the current timestamp.

    This timestamp has  a modular scope so that every test case uses the same timestamp.
    That is important to ensure that one execution of all test cases is stored under the
    same key.

    :return: The current timestamp.
    """
    return datetime.now()


@pytest.fixture(scope="function")
def result_data_handler(test_time_stamp: datetime) -> ResultPersistenceInterface:
    """Returns an instance of ResultPersistenceInterface for storing experiment results.

    This fixture is used to store the results of the performance tests in a persistent
    way with a function scope to ensure that all test cases can run independently.

    Parameters:
        test_time_stamp (datetime): The timestamp of the test.

    Returns:
        ResultPersistenceInterface: An instance of ResultPersistenceInterface.

    """
    return S3ExperimentResultPersistence(test_time_stamp)


@pytest.mark.parametrize("scenario", combine_simulations())
def test_performance_test(
    scenario: TestCase, result_data_handler: ResultPersistenceInterface
) -> None:
    """Run the performance test for the given scenario."""
    simulation_results = scenario.execute_testcase()
    result_data_handler.persist_new_result(scenario.unique_id, simulation_results)
    assert False  # This is a placeholder for the actual test
