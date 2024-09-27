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


@pytest.fixture(scope="module")
def test_time_stamp() -> datetime:
    return datetime.now()


@pytest.mark.parametrize("scenario", combine_simulations())
def test_performance_test(scenario: TestCase, test_time_stamp: datetime) -> None:
    """Run the performance test for the given scenario."""
    result_data_handler: ResultPersistenceInterface = S3ExperimentResultPersistence(
        date_time=test_time_stamp
    )
    simulation_results = scenario.execute_testcase()
    result_data_handler.persist_new_result(scenario.unique_id, simulation_results)
    print(result_data_handler.load_compare_result(scenario.unique_id))
    assert False  # This is a placeholder for the actual test
