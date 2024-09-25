"""This module contains the test cases for simulating scenarios.

The `SCENARIO_TEST_CASES` variable is a list of `SimulateScenariosTestCase` objects.
"""

from typing import List
from uuid import UUID

from baybe.campaign import Campaign
from baybe.objective import SingleTargetObjective
from baybe.searchspace import SearchSpace
from baybe.targets import NumericalTarget, TargetMode
from tests.performance_tests.test_logic.testcases_classes import (
    SimulateScenariosTestCase,
)
from tests.performance_tests.testcases import (
    LOOKUP_STRUCTURE,
    PARAMETER_COMBINATION,
)

SCENARIO_TEST_CASES: List[SimulateScenariosTestCase] = [
    SimulateScenariosTestCase(
        UUID("abefe05d-b6ca-45cf-a9fa-1dce9144eadc"),
        {
            "Mordred": Campaign(
                searchspace=SearchSpace.from_product(
                    parameters=PARAMETER_COMBINATION["direct_arylation_mordred"],
                ),
                objective=SingleTargetObjective(
                    target=NumericalTarget(name="yield", mode=TargetMode.MAX)
                ),
            ),
            "": Campaign(
                searchspace=SearchSpace.from_product(
                    parameters=PARAMETER_COMBINATION["direct_arylation_rdkit"],
                ),
                objective=SingleTargetObjective(
                    target=NumericalTarget(name="yield", mode=TargetMode.MAX)
                ),
            ),
        },
        lookup=LOOKUP_STRUCTURE["direct_arylation"],
        batch_size=2,
        n_doe_iterations=60,
    )
]
