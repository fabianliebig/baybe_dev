"""Data classes that are used to define the test cases for the performance tests.

This file contains helper classes which contain all the necessary information to run a
testcase. One interface is defined to execute the in a uniform way and provide the
possibility to evaluate the results of the testcase not only by its return value but
also by other non functional properties like runtime or memory consumption in
future implementations.
"""

import json
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Literal
from uuid import UUID

from attrs import define
from pandas import DataFrame

from baybe.campaign import Campaign
from baybe.simulation import (
    simulate_experiment,
    simulate_scenarios,
    simulate_transfer_learning,
)


@define
class MetaDataAndResultPerformanceTest:
    """A class to store the metadata and the result of a test case."""

    result: DataFrame
    unique_id: UUID
    title: str
    execution_time_ns: int
    metadata: dict[str, Any]

    def _sanitize_metadata(self) -> dict[str, str]:
        """Sanitize metadata dictionary.

        Remove all None values, convert all values to strings and replace illegal
        characters in the keys and values.
        """
        valid_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-.^_`~|"
        )

        return_dict = {}
        for key, value in self.metadata.items():
            if value is not None:
                sanitized_key = "".join(
                    char if char in valid_chars else "_" for char in key
                )
                return_dict[sanitized_key] = str(value)
        return return_dict

    def to_s3_dict(self) -> dict[str, str]:
        """Convert the object to a dictionary without the dataframe result."""
        removed_none_metadata: dict[str, str] = self._sanitize_metadata()
        removed_none_metadata["unique_id"] = str(self.unique_id)
        removed_none_metadata["title"] = self.title
        removed_none_metadata["execution_time_nanosec"] = str(self.execution_time_ns)
        return removed_none_metadata

    def to_json(self) -> str:
        """Convert the object to a JSON string."""
        return json.dumps(self.to_s3_dict())


@define
class PerformanceTestCase(ABC):
    """Baseinterface for performance test cases."""

    unique_id: UUID
    """A unique identifier for the testcase which is used to
    compare the results over time. A UUID object is used which must be created
    and set manually"""
    title: str
    """A title for the testcase which describes the purpose of the testcase."""

    @abstractmethod
    def execute_testcase(self) -> MetaDataAndResultPerformanceTest:
        """Run the testcase.

        The method actually starts the performance test and returns the result
        as a pandas DataFrame. This enables potential future evaluations types
        like runtime or memory consumption during the test.
        """
        pass


@define
class SimulateScenariosTestCase(PerformanceTestCase):
    """Testcase for the simulate_scenarios function.

    This testcase makes use of the simulate_scenarios function more can be
    found in the documentation of the function
    under :func:`baybe.simulation.scenarios.simulate_scenarios`
    """

    scenarios: dict[Any, Campaign]
    lookup: DataFrame | Callable | None = None
    batch_size: int = 1
    n_doe_iterations: int | None = None
    initial_data: list[DataFrame] | None = None
    groupby: list[str] | None = None
    n_mc_iterations: int = 1
    random_seed: int | None = None
    impute_mode: Literal["error", "worst", "best", "mean", "random", "ignore"] = (
        "random"
    )
    noise_percent: float | None = None

    def execute_testcase(self) -> MetaDataAndResultPerformanceTest:
        """Execute the simulate_scenarios testcase.

        See :func:`baybe.simulation.scenarios.simulate_scenarios` for more information.
        """
        start_time = time.perf_counter_ns()
        result = simulate_scenarios(
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
        end_time = time.perf_counter_ns()
        execution_time = end_time - start_time
        return MetaDataAndResultPerformanceTest(
            execution_time_ns=execution_time,
            result=result,
            unique_id=self.unique_id,
            title=self.title,
            metadata={
                "DOE iterations": self.n_doe_iterations,
                "batch size": self.batch_size,
                "groupby": self.groupby,
                "MC iterations": self.n_mc_iterations,
                "impute mode": self.impute_mode,
                "noise percent": self.noise_percent,
                "random seed": self.random_seed,
            },
        )


@define
class SimulateTransferLearningTestCase(PerformanceTestCase):
    """Testcase for the simulate_transfer_learning function.

    This testcase makes use of the simulate_transfer_learning function more can be
    found in the documentation of the function
    under :func:`baybe.simulation.transfer_learning.simulate_transfer_learning`
    """

    @staticmethod
    def _validate_lookup(lookup: DataFrame) -> bool:
        """Validate the lookup DataFrame.

        The lookup DataFrame must have the columns "source" and "target" and
        the column "source" must be unique. If the DataFrame is not valid
        a ValueError is raised.

        Args:
            lookup: The lookup DataFrame to validate.

        Returns:
            DataFrame: The validated lookup DataFrame.
        """
        return isinstance(lookup, DataFrame)

    campaign: Campaign
    lookup: DataFrame
    batch_size: int = 1
    n_doe_iterations: int | None = None
    groupby: list[str] | None = None
    n_mc_iterations: int = 1

    def execute_testcase(self) -> MetaDataAndResultPerformanceTest:
        """Execute the simulate_transfer_learning testcase.

        See :func:`baybe.simulation.transfer_learning.simulate_transfer_learning`
        for more information.
        """
        start_time = time.perf_counter_ns()
        result = simulate_transfer_learning(
            self.campaign,
            self.lookup,
            batch_size=self.batch_size,
            n_doe_iterations=self.n_doe_iterations,
            groupby=self.groupby,
            n_mc_iterations=self.n_mc_iterations,
        )
        end_time = time.perf_counter_ns()
        execution_time = end_time - start_time
        return MetaDataAndResultPerformanceTest(
            execution_time_ns=execution_time,
            result=result,
            unique_id=self.unique_id,
            title=self.title,
            metadata={
                "DOE iterations": self.n_doe_iterations,
                "batch size": self.batch_size,
                "groupby": self.groupby,
                "MC iterations": self.n_mc_iterations,
            },
        )


@define
class SimulateExperimentTestCase(PerformanceTestCase):
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
    impute_mode: Literal["error", "worst", "best", "mean", "random", "ignore"] = (
        "random"
    )
    noise_percent: float | None = None

    def execute_testcase(self) -> MetaDataAndResultPerformanceTest:
        """Execute the simulate_experiment testcase.

        See :func:`baybe.simulation.core.simulate_experiment`
        for more information.
        """
        start_time = time.perf_counter_ns()
        result = simulate_experiment(
            self.campaign,
            self.lookup,
            batch_size=self.batch_size,
            n_doe_iterations=self.n_doe_iterations,
            initial_data=self.initial_data,
            random_seed=self.random_seed,
            impute_mode=self.impute_mode,
            noise_percent=self.noise_percent,
        )
        end_time = time.perf_counter_ns()
        execution_time = end_time - start_time
        return MetaDataAndResultPerformanceTest(
            execution_time_ns=execution_time,
            result=result,
            unique_id=self.unique_id,
            title=self.title,
            metadata={
                "DOE iterations": self.n_doe_iterations,
                "batch size": self.batch_size,
                "impute mode": self.impute_mode,
                "noise percent": self.noise_percent,
                "random seed": self.random_seed,
            },
        )
