"""Test module for the S3ExperimentResultPersistence class."""

import io
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import pandas as pd
import pytest

from tests.performance_tests.utils.data_handling_classes import (
    S3ExperimentResultPersistence,
)
from tests.performance_tests.utils.testcases_classes import (
    MetaDataAndResultPerformanceTest,
)


@pytest.fixture
def s3_persistence() -> S3ExperimentResultPersistence:
    return S3ExperimentResultPersistence(
        date_time=datetime.now(),
        branch="main",
        bucket_name="bucket",
        commit_hash="hash",
        baybe_version="1.2.5",
    )


def test_sanitize_baybe_version_no_post_release(
    s3_persistence: S3ExperimentResultPersistence,
):
    version = "1.2.3"
    sanitized_version = s3_persistence._sanitize_baybe_version(version)
    assert sanitized_version == "1.2.3"


def test_sanitize_baybe_version_with_post_release(
    s3_persistence: S3ExperimentResultPersistence,
):
    version = "1.2.3.4"
    sanitized_version = s3_persistence._sanitize_baybe_version(version)
    assert sanitized_version == "1.2.3"


def test_sanitize_baybe_version_with_multiple_post_release(
    s3_persistence: S3ExperimentResultPersistence,
):
    version = "1.2.3.4.5"
    sanitized_version = s3_persistence._sanitize_baybe_version(version)
    assert sanitized_version == "1.2.3"


def test_sanitize_baybe_version_with_pre_release(
    s3_persistence: S3ExperimentResultPersistence,
):
    version = "1.2.3-alpha"
    sanitized_version = s3_persistence._sanitize_baybe_version(version)
    assert sanitized_version == "1.2.3-alpha"


def test_sanitize_baybe_version_with_pre_and_post_release(
    s3_persistence: S3ExperimentResultPersistence,
):
    version = "1.2.3-alpha.4"
    sanitized_version = s3_persistence._sanitize_baybe_version(version)
    assert sanitized_version == "1.2.3-alpha"


def test_persist_new_result(s3_persistence: S3ExperimentResultPersistence):
    experiment_id = UUID("12345678123456781234567812345678")
    result = MagicMock(spec=MetaDataAndResultPerformanceTest)
    result.to_s3_dict.return_value = {"key": "value"}
    result.result.to_csv.return_value = "csv_data"

    with patch.object(s3_persistence._object_session, "client") as mock_client:
        s3_persistence.persist_new_result(experiment_id, result)
        mock_client().put_object.assert_called_once()


def test_load_compare_result_main_branch(s3_persistence: S3ExperimentResultPersistence):
    experiment_id = UUID("12345678123456781234567812345678")

    with patch(
        "tests.performance_tests.utils.data_handling_classes.S3ExperimentResultPersistence._get_newest_dataset_from_last_release"
    ) as mock_method:
        s3_persistence.load_compare_result(experiment_id)
        mock_method.assert_called_once_with(experiment_id)


def test_load_compare_result_non_main_branch(
    s3_persistence: S3ExperimentResultPersistence,
):
    experiment_id = UUID("12345678123456781234567812345678")
    s3_persistence.branch = "feature-branch"

    with patch(
        "tests.performance_tests.utils.data_handling_classes.S3ExperimentResultPersistence._get_current_main_newest_result"
    ) as mock_method:
        s3_persistence.load_compare_result(experiment_id)
        mock_method.assert_called_once_with(experiment_id)


def test_get_latest_available_release(s3_persistence: S3ExperimentResultPersistence):
    experiment_id = UUID("12345678123456781234567812345678")

    with patch.object(s3_persistence._object_session, "client") as mock_client:
        mock_client().get_paginator().paginate.return_value = iter(
            [{"Contents": [{"Key": "key1/main/1.2.3-pre"}, {"Key": "key2/main/1.2.4"}]}]
        )
        last_release = s3_persistence._get_last_available_release(experiment_id)
        assert last_release == "1.2.4"


def test_get_previous_available_release(s3_persistence: S3ExperimentResultPersistence):
    experiment_id = UUID("12345678123456781234567812345678")
    s3_persistence.baybe_version = "1.2.4"
    with patch.object(s3_persistence._object_session, "client") as mock_client:
        mock_client().get_paginator().paginate.return_value = iter(
            [{"Contents": [{"Key": "key1/main/1.2.3"}, {"Key": "key2/main/1.2.4"}]}]
        )
        last_release = s3_persistence._get_last_available_release(experiment_id)
        assert last_release == "1.2.3"


def test_retrieve_dataframe_from_s3(s3_persistence: S3ExperimentResultPersistence):
    key = "some/key"

    with patch.object(s3_persistence._object_session, "client") as mock_client:
        mock_client().get_object.return_value = {
            "Body": io.BytesIO(b"col1,col2\nval1,val2")
        }
        df = s3_persistence._retrieve_dataframe_from_s3(key)
        assert isinstance(df, pd.DataFrame)
        assert df.equals(pd.DataFrame({"col1": ["val1"], "col2": ["val2"]}))


def test_get_newest_s3_object_with_results(
    s3_persistence: S3ExperimentResultPersistence,
):
    iterator = [
        {
            "Contents": [
                {"Key": "key1", "LastModified": datetime(2023, 1, 1)},
                {"Key": "key2", "LastModified": datetime(2023, 1, 2)},
            ]
        }
    ]

    newest_object = s3_persistence._get_newest_s3_object(iterator)  # type: ignore
    assert newest_object["Key"] == "key2"


def test_get_newest_s3_object_no_results(s3_persistence: S3ExperimentResultPersistence):
    iterator = iter([{"Contents": []}])

    with pytest.raises(
        ValueError, match="No result found for the given experiment ID."
    ):
        s3_persistence._get_newest_s3_object(iterator)  # type: ignore


def test_get_newest_s3_object_multiple_pages(
    s3_persistence: S3ExperimentResultPersistence,
):
    iterator = iter(
        [
            {
                "Contents": [
                    {"Key": "key1", "LastModified": datetime(2023, 1, 1)},
                    {"Key": "key2", "LastModified": datetime(2023, 1, 2)},
                ]
            },
            {
                "Contents": [
                    {"Key": "key3", "LastModified": datetime(2023, 1, 3)},
                    {"Key": "key4", "LastModified": datetime(2023, 1, 4)},
                ]
            },
        ]
    )

    newest_object = s3_persistence._get_newest_s3_object(iterator)  # type: ignore
    assert newest_object["Key"] == "key4"
