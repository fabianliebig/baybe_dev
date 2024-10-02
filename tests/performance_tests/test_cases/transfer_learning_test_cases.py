"""This module contains test cases for transfer learning simulation.

Attributes:
    TRANSFER_LEARNING_TEST_CASES (Sequence): A list of SimulateTransferLearningTestCase
    objects representing the test cases.
"""

from typing import List
from uuid import UUID

from pandas import DataFrame

from baybe.campaign import Campaign
from baybe.objective import SingleTargetObjective
from baybe.searchspace import SearchSpace
from baybe.targets import NumericalTarget, TargetMode
from tests.performance_tests.test_cases import (
    LOOKUP_STRUCTURE,
    PARAMETER_COMBINATION,
)
from tests.performance_tests.utils import (
    SimulateTransferLearningTestCase,
)

TRANSFER_LEARNING_TEST_CASES: List[SimulateTransferLearningTestCase] = [
    SimulateTransferLearningTestCase(
        unique_id=UUID("c3cb1de4-f631-493b-94a8-1dfcd67f13cb"),
        title="Cell Media Simulation maximum titer",
        campaign=Campaign(
            searchspace=SearchSpace.from_product(
                parameters=PARAMETER_COMBINATION["hartmann_function"]
            ),
            objective=SingleTargetObjective(
                target=NumericalTarget(name="Target", mode=TargetMode.MIN)
            ),
        ),
        lookup=LOOKUP_STRUCTURE["hartmann_function"],
        batch_size=2,
        n_doe_iterations=10,
        n_mc_iterations=30,
    )
]
