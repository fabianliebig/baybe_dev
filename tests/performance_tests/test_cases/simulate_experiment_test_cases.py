"""SimulateExperimentTestCase.

This module contains a test case for simulating an experiment.

Attributes:
    SIMULATE_EXPERIMENT_TEST_CASES (Sequence): A list of SimulateExperimentTestCase objects.
"""

from typing import List
from uuid import UUID

from baybe.campaign import Campaign
from baybe.objective import SingleTargetObjective
from baybe.searchspace import SearchSpace
from baybe.targets import NumericalTarget, TargetMode
from tests.performance_tests.test_cases import (
    LOOKUP_STRUCTURE,
    PARAMETER_COMBINATION,
)
from tests.performance_tests.utils import (
    SimulateExperimentTestCase,
)

SIMULATE_EXPERIMENT_TEST_CASES: List[SimulateExperimentTestCase] = [
    SimulateExperimentTestCase(
        unique_id=UUID("23df40f6-243c-49ca-ae71-81d733d8a88d"),
        title="Aryl Halides Simulation maximum yield with Mordred",
        campaign=Campaign(
            searchspace=SearchSpace.from_product(
                parameters=PARAMETER_COMBINATION["aryl_halides_mordred"],
            ),
            objective=SingleTargetObjective(
                target=NumericalTarget(name="yield", mode=TargetMode.MAX)
            ),
        ),
        lookup=LOOKUP_STRUCTURE["aryl_halides"],
        batch_size=2,
        n_doe_iterations=60,
    )
]
