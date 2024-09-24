"""End-to-end tests for the performance of the baybe package.

Tests the performacnce of the baybe package by executing long running and compute
intensive example szenarios and persisting the results so that they can be
compared between different versions of the package.
"""

import os

import pytest

from tests.performance_tests.test_logic.testcases_classes import TestCase
from tests.performance_tests.testcases import (
    SCENARIO_TEST_CASES,
    SIMULATE_EXPERIMENT_TEST_CASES,
    TRANSPHER_LEARNING_TEST_CASES,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("BAYBE_TEST_ENV") != "PERFORMANCETEST",
    reason="Only possible in PERFORMANCETEST environment.",
)


def combine_simulations() -> list[TestCase]:
    """Combines different sets of test cases into a single list.

    Returns:
        list[TestCase]: A list containing all the test cases from SCENARIO_TEST_CASES,
        SIMULATE_EXPERIMENT_TEST_CASES, and TRANSPHER_LEARNING_TEST_CASES.
    """
    return (
        SCENARIO_TEST_CASES
        + SIMULATE_EXPERIMENT_TEST_CASES
        + TRANSPHER_LEARNING_TEST_CASES
    )


@pytest.mark.parametrize("scenario", combine_simulations())
def test_performance_test(scenario: TestCase):
    """Run the performance test for the given scenario."""
    print(scenario.execute_testcase())
    assert False  # This is a placeholder for the actual test
