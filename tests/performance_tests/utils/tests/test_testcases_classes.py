"""Test cases for the performance tests classes."""

from typing import Callable, List
from uuid import UUID, uuid4

import pytest
from pandas import DataFrame

from baybe.campaign import Campaign
from baybe.objective import SingleTargetObjective
from baybe.parameters.base import Parameter
from baybe.parameters.substance import SubstanceEncoding, SubstanceParameter
from baybe.searchspace.core import SearchSpace
from baybe.targets import NumericalTarget, TargetMode
from tests.performance_tests.test_cases import (
    LOOKUP_STRUCTURE,
    PARAMETER_COMBINATION,
)
from tests.performance_tests.utils.testcases_classes import (
    SimulateExperimentTestCase,
    SimulateScenariosTestCase,
    SimulateTransferLearningTestCase,
    TestMetaDataAndResult,
)


@pytest.fixture
def sample_dataframe() -> DataFrame | Callable:
    dataframe_fixture = LOOKUP_STRUCTURE["hartmann_function"]
    return dataframe_fixture


@pytest.fixture
def sample_campaign():
    parameter = PARAMETER_COMBINATION["hartmann_function"]
    return Campaign(
        searchspace=SearchSpace.from_product(parameters=parameter),
        objective=SingleTargetObjective(
            target=NumericalTarget(name="Target", mode=TargetMode.MIN)
        ),
    )


@pytest.fixture
def sample_uuid():
    return uuid4()


def test_metadata_and_result_to_s3_dict(sample_dataframe: DataFrame, sample_uuid: UUID):
    metadata = {"key1": "value1", "key2": None}
    test_metadata_and_result = TestMetaDataAndResult(
        result=sample_dataframe,
        unique_id=sample_uuid,
        title="Sample Title",
        metadata=metadata,
    )
    s3_dict = test_metadata_and_result.to_s3_dict()
    assert s3_dict["unique_id"] == str(sample_uuid)
    assert s3_dict["title"] == "Sample Title"
    assert "key1" in s3_dict
    assert "key2" not in s3_dict


def test_simulate_scenarios_testcase_execute_testcase(
    sample_campaign: Campaign, sample_dataframe: DataFrame, sample_uuid: UUID
):
    scenarios = {"scenario1": sample_campaign}
    test_case = SimulateScenariosTestCase(
        unique_id=sample_uuid,
        title="Simulate Scenarios Test",
        scenarios=scenarios,
        lookup=sample_dataframe,
        n_doe_iterations=1,
    )
    result = test_case.execute_testcase()
    assert isinstance(result, TestMetaDataAndResult)
    assert result.unique_id == sample_uuid
    assert result.title == "Simulate Scenarios Test"


def test_simulate_transfer_learning_testcase_execute_testcase(
    sample_campaign: Campaign, sample_dataframe: DataFrame, sample_uuid: UUID
):
    test_case = SimulateTransferLearningTestCase(
        unique_id=sample_uuid,
        title="Simulate Transfer Learning Test",
        campaign=sample_campaign,
        lookup=sample_dataframe,
        n_doe_iterations=1,
    )
    result = test_case.execute_testcase()
    assert isinstance(result, TestMetaDataAndResult)
    assert result.unique_id == sample_uuid
    assert result.title == "Simulate Transfer Learning Test"


def test_simulate_experiment_testcase_execute_testcase(
    sample_campaign: Campaign, sample_dataframe: DataFrame, sample_uuid: UUID
):
    test_case = SimulateExperimentTestCase(
        unique_id=sample_uuid,
        title="Simulate Experiment Test",
        campaign=sample_campaign,
        lookup=sample_dataframe,
        n_doe_iterations=1,
    )
    result = test_case.execute_testcase()
    assert isinstance(result, TestMetaDataAndResult)
    assert result.unique_id == sample_uuid
    assert result.title == "Simulate Experiment Test"
