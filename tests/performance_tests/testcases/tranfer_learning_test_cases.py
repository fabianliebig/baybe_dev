"""This module contains test cases for transfer learning simulation.

Attributes:
    TRANSPHER_LEARNING_TEST_CASES (list): A list of SimulateTransferLearningTestCase
    objects representing the test cases.
"""

from typing import List
from uuid import UUID

from baybe.campaign import Campaign
from baybe.objective import SingleTargetObjective
from baybe.searchspace import SearchSpace
from baybe.targets import NumericalTarget, TargetMode
from tests.performance_tests.test_logic.testcases_classes import (
    SimulateTransferLearningTestCase,
)
from tests.performance_tests.testcases import (
    LOOKUP_STRUCTURE,
    PARAMETER_COMBINATION,
)

TRANSPHER_LEARNING_TEST_CASES: List[SimulateTransferLearningTestCase] = [
    SimulateTransferLearningTestCase(
        UUID("abefe05d-b6ca-45cf-a9fa-1dce9144eadc"),
        Campaign(
            searchspace=SearchSpace.from_product(
                parameters=PARAMETER_COMBINATION["direct_arylation_mordred"],
            ),
            objective=SingleTargetObjective(
                target=NumericalTarget(name="yield", mode=TargetMode.MAX)
            ),
        ),
        lookup=LOOKUP_STRUCTURE["direct_arylation"],
        batch_size=2,
        n_doe_iterations=60,
    )
]
