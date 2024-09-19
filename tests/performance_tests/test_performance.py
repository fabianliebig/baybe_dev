"""End-to-end tests for the performance of the baybe package.

Tests the performacnce of the baybe package by executing long running and compute
intensive example szenarios and persisting the results so that they can be
compared between different versions of the package.
"""

import json
import os

import pytest

from tests.performance_tests.test_logic.testcases_classes import (
    TestCase,
    TypeOfTestCase,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("BAYBE_TEST_ENV") != "PERFORMANCETEST",
    reason="Only possible in PERFORMANCETEST environment.",
)


def get_json_testcase_pathes() -> list[str]:
    """Get the pathes to the json files containing the testcases.

    Returns:
        list[str]: A list of file paths to the json files containing the testcases.
    """
    RELATIVE_FOLDER_PATH = "tests/performance_tests/testcases"
    return [
        RELATIVE_FOLDER_PATH + "/" + file
        for file in os.listdir(RELATIVE_FOLDER_PATH)
        if file.endswith(".json")
    ]


def load_scenarios() -> list[TestCase]:
    """Load the scenarios from the json file.

    This function is used to load the scenarios from the json files in the
    testcases folder. The scenarios are seperated by the type of testcase
    which are defined in the TypeOfTestCase enum. There, the corresponding
    string representation of the type is used to get the correct class to
    load the testcase and prepare it for the test run.

    Returns:
        List[TestCase]: A list of test cases loaded from the json files.
    """
    test_cases = []
    list_of_json_files = get_json_testcase_pathes()
    for file_path in list_of_json_files:
        with open(file_path) as json_file:
            testcase = json.load(json_file)
            case_type = testcase["type"]
            test_case_class = TypeOfTestCase.get_test_case_class(case_type)
            test_cases.append(test_case_class.from_json(testcase))
    return test_cases


@pytest.mark.parametrize("scenario", load_scenarios())
def test_performance_test(scenario: TestCase):
    """Run the performance test for the given scenario."""
    print(scenario.execute_testcase())
    assert 1 == 0
