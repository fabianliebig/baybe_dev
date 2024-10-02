"""Test cases for the performance tests classes."""
from typing import List
from uuid import uuid4

import pytest
from pandas import DataFrame

from baybe.campaign import Campaign
from baybe.parameters.base import Parameter
from baybe.parameters.substance import SubstanceEncoding, SubstanceParameter
from baybe.searchspace.core import SearchSpace
from tests.performance_tests.utils.testcases_classes import (
    SimulateExperimentTestCase,
    SimulateScenariosTestCase,
    SimulateTransferLearningTestCase,
    MetaDataAndResultPerformanceTest,
)


@pytest.fixture
def sample_dataframe():
    return DataFrame({"col1": [1, 2], "col2": [3, 4]})


@pytest.fixture
def sample_campaign():
    parameter: List[Parameter] = [
        SubstanceParameter(
            name="base",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "BTMG": "CN(C)/C(N(C)C)=N\\C(C)(C)C",
                "MTBD": "CN1CCCN2CCCN=C12",
                "P2Et": "CN(C)P(N(C)C)(N(C)C)=NP(N(C)C)(N(C)C)=NCC",
            },
        ),
        SubstanceParameter(
            name="ligand",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "XPhos": "CC(C)C1=CC(C(C)C)=CC(C(C)C)=C1C2=C(P(C3"
                "CCCCC3)C4CCCCC4)C=CC=C2",
                "t-BuXPhos": "CC(C)C(C=C(C(C)C)C=C1C(C)C)=C1C2=CC=CC=C2P(C(C)"
                "(C)C)C(C)(C)C",
                "t-BuBrettPhos": "CC(C)C1=CC(C(C)C)=CC(C(C)C)=C1C2=C(P(C(C)(C)C)C(C)"
                "(C)C)C(OC)=CC=C2OC",
                "AdBrettPhos": "CC(C1=C(C2=C(OC)C=CC(OC)=C2P(C34CC5CC(C4)CC(C5)C3)C67"
                "CC8CC(C7)CC(C8)C6)C(C(C)C)=CC(C(C)C)=C1)C",
            },
        ),
    ]
    return Campaign(searchspace=SearchSpace.from_product(parameters=parameter))


@pytest.fixture
def sample_uuid():
    return uuid4()


def test_metadata_and_result_to_s3_dict(sample_dataframe, sample_uuid):
    metadata = {"key1": "value1", "key2": None}
    test_metadata_and_result = MetaDataAndResultPerformanceTest(
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
    sample_campaign, sample_dataframe, sample_uuid
):
    scenarios = {"scenario1": sample_campaign}
    test_case = SimulateScenariosTestCase(
        unique_id=sample_uuid,
        title="Simulate Scenarios Test",
        scenarios=scenarios,
        lookup=sample_dataframe,
    )
    result = test_case.execute_testcase()
    assert isinstance(result, MetaDataAndResultPerformanceTest)
    assert result.unique_id == sample_uuid
    assert result.title == "Simulate Scenarios Test"


def test_simulate_transfer_learning_testcase_execute_testcase(
    sample_campaign, sample_dataframe, sample_uuid
):
    test_case = SimulateTransferLearningTestCase(
        unique_id=sample_uuid,
        title="Simulate Transfer Learning Test",
        campaign=sample_campaign,
        lookup=sample_dataframe,
    )
    result = test_case.execute_testcase()
    assert isinstance(result, MetaDataAndResultPerformanceTest)
    assert result.unique_id == sample_uuid
    assert result.title == "Simulate Transfer Learning Test"


def test_simulate_experiment_testcase_execute_testcase(
    sample_campaign, sample_dataframe, sample_uuid
):
    test_case = SimulateExperimentTestCase(
        unique_id=sample_uuid,
        title="Simulate Experiment Test",
        campaign=sample_campaign,
        lookup=sample_dataframe,
    )
    result = test_case.execute_testcase()
    assert isinstance(result, MetaDataAndResultPerformanceTest)
    assert result.unique_id == sample_uuid
    assert result.title == "Simulate Experiment Test"
