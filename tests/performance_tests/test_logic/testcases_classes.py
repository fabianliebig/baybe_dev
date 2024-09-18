"""Data classes that are used to define the test cases for the performance tests.

This file contains helper classes which contain all the necessary information to run a
testcase. One interface is defined to execute the in a uniform way and profide the
possibility to evaluate the results of the testcase not only by its return value but
also by other non functional properties like runtime or memory consumption in
furture implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any, Literal

from attrs import define
from pandas import DataFrame

from baybe.campaign import Campaign
from baybe.simulation import (
    simulate_experiment,
    simulate_scenarios,
    simulate_transfer_learning,
)


@define
class TestCase(ABC):
    """Baseinterface for performance test cases."""

    @classmethod
    @abstractmethod
    def from_json(cls, json_dict: dict[str, Any]) -> "TestCase":
        """Load a testcase from a json dictionary.

        This method is used to load a testcase from a json dictionary. Depending
        on the implemeting class the json dictionary can contain different keys. The
        necessary keys schemas can be found in the attached readme file.
        """
        pass

    @abstractmethod
    def execute_testcase(self) -> DataFrame:
        """Run the testcase.

        The method actually starts the performance test and returns the result
        as a pandas DataFrame. This enables potential future evaluations types
        like runtime or memory consumption during the test.
        """
        pass


@define
class SimulateScenariosTestCase(TestCase):
    """Testcase for the simulate_scenarios function.

    This testcase makes use of the simulate_scenarios function more can be
    found in the documentation of the function
    under :func:`baybe.simulation.scenarios.simulate_scenarios`
    """

    scenarios: dict[Any, Campaign]
    lookup: DataFrame | None = None
    batch_size: int = 1
    n_doe_iterations: int | None = None
    initial_data: list[DataFrame] | None = None
    groupby: list[str] | None = None
    n_mc_iterations: int = 1
    random_seed: int | None = None
    impute_mode: Literal["error", "worst", "best", "mean", "random", "ignore"] = "error"
    noise_percent: float | None = None
    description: str | None = None
    type: str | None = None

    @classmethod
    def from_json(cls, json_dict: dict[str, Any]) -> "SimulateScenariosTestCase":
        lookup = json_dict.pop("lookup", None)
        szenarios = json_dict.pop("scenarios", None)
        initial_data = json_dict.pop("initial_data", None)
        if lookup is not None:
            lookup = DataFrame(lookup)
        if szenarios is not None:
            scenarios = {
                key: Campaign.from_dict(value) for key, value in szenarios.items()
            }
        if initial_data is not None:
            initial_data = [DataFrame(data) for data in initial_data]
        return cls(
            scenarios=scenarios, lookup=lookup, initial_data=initial_data, **json_dict
        )

    def execute_testcase(self) -> DataFrame:
        """Execute the simulate_scenarios testcase.

        See :func:`baybe.simulation.scenarios.simulate_scenarios` for more information.
        """
        return simulate_scenarios(
            self.scenarios,
            self.lookup,
            batch_size=self.batch_size,
            n_doe_iterations=self.n_doe_iterations,
            initial_data=self.initial_data,
            groupby=self.groupby,
            n_mc_iterations=self.n_mc_iterations,
            random_seed=self.random_seed,
            impute_mode=self.impute_mode,
            noise_percent=self.noise_percent,
        )


@define
class SimulateTransferLearningTestCase(TestCase):
    """Testcase for the simulate_transfer_learning function.

    This testcase makes use of the simulate_transfer_learning function more can be
    found in the documentation of the function
    under :func:`baybe.simulation.transfer_learning.simulate_transfer_learning`
    """

    campaign: Campaign
    lookup: DataFrame
    batch_size: int = 1
    n_doe_iterations: int | None = None
    groupby: list[str] | None = None
    n_mc_iterations: int = 1
    description: str | None = None
    type: str | None = None

    @classmethod
    def from_json(cls, json_dict: dict[str, Any]) -> "SimulateTransferLearningTestCase":
        lookup = json_dict.pop("lookup", None)
        campaign = json_dict.pop("campaign", None)
        if lookup is not None:
            lookup = DataFrame(lookup)
        if campaign is not None:
            campaign = Campaign.from_dict(campaign)
        return cls(campaign=campaign, lookup=lookup, **json_dict)

    def execute_testcase(self) -> DataFrame:
        """Execute the simulate_transfer_learning testcase.

        See :func:`baybe.simulation.transfer_learning.simulate_transfer_learning`
        for more information.
        """
        return simulate_transfer_learning(
            self.campaign,
            self.lookup,
            batch_size=self.batch_size,
            n_doe_iterations=self.n_doe_iterations,
            groupby=self.groupby,
            n_mc_iterations=self.n_mc_iterations,
        )


@define
class SimulateExperimentTestCase(TestCase):
    """Testcase for the simulate_experiment function.

    This testcase makes use of the simulate_experiment function more can be
    found in the documentation of the function
    under :func:`baybe.simulation.core.simulate_experiment`
    """

    campaign: Campaign
    lookup: DataFrame | Callable | None = None
    batch_size: int = 1
    n_doe_iterations: int | None = None
    initial_data: DataFrame | None = None
    random_seed: int | None = None
    impute_mode: Literal["error", "worst", "best", "mean", "random", "ignore"] = "error"
    noise_percent: float | None = None
    description: str | None = None
    type: str | None = None

    @classmethod
    def from_json(cls, json_dict: dict[str, Any]) -> "SimulateExperimentTestCase":
        lookup = json_dict.pop("lookup", None)
        campaign = json_dict.pop("campaign", None)
        initial_data = json_dict.pop("initial_data", None)
        if lookup is not None:
            lookup = DataFrame(lookup)
        if campaign is not None:
            campaign = Campaign.from_dict(campaign)
        if initial_data is not None:
            initial_data = DataFrame(initial_data)
        return cls(
            campaign=campaign, lookup=lookup, initial_data=initial_data, **json_dict
        )

    def execute_testcase(self) -> DataFrame:
        """Execute the simulate_experiment testcase.

        See :func:`baybe.simulation.core.simulate_experiment`
        for more information.
        """
        return simulate_experiment(
            self.campaign,
            self.lookup,
            batch_size=self.batch_size,
            n_doe_iterations=self.n_doe_iterations,
            initial_data=self.initial_data,
            random_seed=self.random_seed,
            impute_mode=self.impute_mode,
            noise_percent=self.noise_percent,
        )


class TypeOfTestCase(Enum):
    """Enum for the different types of testcases.

    Returns the corresponding test case class based on the given case_type.
    """

    SIMULATE_EXPERIMENT = "SimulateExperiment"
    SIMULATE_SCENARIOS = "SimulateScenarios"
    SIMULATE_TRANSFER_LEARNING = "SimulateTransferLearning"

    @staticmethod
    def get_test_case_class(case_type: str) -> type[TestCase]:
        """Returns the test case class based on the given case_type.

        Parameters:
            case_type (str): The type of the test case which  will likely be part of the
            loaded testcase json and indicated by the key `type`.

        Returns:
            type[TestCase]: The test case class corresponding to the case_type.

        Raises:
            ValueError: If the case_type is unknown.
        """
        if case_type == TypeOfTestCase.SIMULATE_EXPERIMENT.value:
            return SimulateExperimentTestCase
        elif case_type == TypeOfTestCase.SIMULATE_SCENARIOS.value:
            return SimulateScenariosTestCase
        elif case_type == TypeOfTestCase.SIMULATE_TRANSFER_LEARNING.value:
            return SimulateTransferLearningTestCase
        else:
            raise ValueError(f"Unknown test case type: {case_type}")
