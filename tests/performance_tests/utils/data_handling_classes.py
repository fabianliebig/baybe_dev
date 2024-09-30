"""Classes for persisting and loading experiment results."""

import io
import os
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

import boto3
import boto3.session
import pandas
from attr import define, field
from botocore.paginate import PageIterator
from pandas import DataFrame

from baybe import __version__
from tests.performance_tests.utils.testcases_classes import TestMetaDataAndResult


@define
class ResultPersistenceInterface(ABC):
    """Interface for classes that persist experiment results."""

    @staticmethod
    def _default_baybe_version() -> str:
        return __version__

    @staticmethod
    def _default_branch() -> str:
        if "GITHUB_REF_NAME" not in os.environ and os.environ:
            raise ValueError("The environment variable GITHUB_REF_NAME is not set.")
        path_usable_branch = os.environ["GITHUB_REF_NAME"].replace("/", "-")
        return path_usable_branch

    @staticmethod
    def _default_commit_hash() -> str:
        if "GITHUB_SHA" not in os.environ:
            raise ValueError("The environment variable GITHUB_SHA is not set.")
        return os.environ["GITHUB_SHA"]

    date_time: datetime
    baybe_version: str = field(default=_default_baybe_version())
    """The version of the Baybe library."""
    branch: str = field(default=_default_branch())
    """The branch of the Baybe library from which the workflow was started."""
    commit_hash: str = field(default=_default_commit_hash())

    @abstractmethod
    def persist_new_result(
        self, experiment_id: UUID, result: TestMetaDataAndResult
    ) -> None:
        """Persists a new result for the given experiment.

        Args:
            experiment_id (UUID): The ID of the experiment.
            result (TestMetaDataAndResult): The result to be persisted.
        """
        pass

    @abstractmethod
    def load_compare_result(self, experiment_id: UUID) -> DataFrame:
        """Load the oldest stable result for a given experiment ID.

        Loads the oldest result from an experiment that is created from the main branch
        of the Baybe library. This is done to compare the performance of the library
        over a longer time period and to ensure that the results don't just a bit from
        version to version which would be not noticeable in the short term.

        Parameters:
            experiment_id (UUID): The ID of the experiment.

        Returns:
            Dataframe: The last result for the given experiment ID.
        """
        pass


@define
class S3ExperimentResultPersistence(ResultPersistenceInterface):
    """Class for persisting experiment results in an S3 bucket."""

    @staticmethod
    def _default_bucket_name() -> str:
        ENVIRONMENT_NOT_SET = (
            "BAYBE_PERFORMANCE_TEST_RESULT_S3_BUCKET_NAME" not in os.environ
        )
        if ENVIRONMENT_NOT_SET:
            raise ValueError(
                "The environment variable "
                "BAYBE_PERFORMANCE_TEST_RESULT_S3_BUCKET_NAME is not set. "
                "A bucket name must be provided."
            )
        return os.environ["BAYBE_PERFORMANCE_TEST_RESULT_S3_BUCKET_NAME"]

    bucket_name: str = field(default=_default_bucket_name())
    """The name of the S3 bucket where the results are stored."""
    _object_session = boto3.session.Session()

    def persist_new_result(
        self, experiment_id: UUID, result: TestMetaDataAndResult
    ) -> None:
        """Persists a new result for the given experiment.

        Args:
            experiment_id (UUID): The ID of the experiment.
            result (TestMetaDataAndResult): The result to be persisted.
        """
        client = self._object_session.client("s3")
        bucket_path = (
            f"{experiment_id}/"
            f"{self.branch}/{self.baybe_version}/{self.date_time.isoformat()}/{self.commit_hash}"
        )

        metadata = result.to_s3_dict()
        metadata["date_time"] = self.date_time.isoformat()

        client.put_object(
            Bucket=self.bucket_name,
            Key=f"{bucket_path}/result.csv",
            Body=result.result.to_csv(),
            ContentType="text/csv",
            Metadata=metadata,
        )

    def _get_oldest_s3_object(self, iterator: PageIterator) -> dict:
        """Retrieves the oldest S3 object from the given iterator.

        Args:
            iterator (PageIterator): An iterator that provides access to S3 objects.

        Returns:
            dict: The oldest S3 object as a dictionary.

        Raises:
            ValueError: If no result is found for the given experiment ID.
        """
        oldest_object = None
        for page in iterator:
            for content in page["Contents"]:
                OBSERVED_CONTENT_IS_OLDER = (
                    oldest_object is not None
                    and content["LastModified"] < oldest_object["LastModified"]
                )
                if not oldest_object or OBSERVED_CONTENT_IS_OLDER:
                    oldest_object = content

        if not oldest_object:
            raise ValueError("No result found for the given experiment ID.")
        return oldest_object

    def load_compare_result(self, experiment_id: UUID) -> DataFrame:
        """Load the oldest stable result for a given experiment ID.

        Loads the oldest result from an experiment that is created from the main branch
        of the Baybe library. This is done to compare the performance of the library
        over a longer time period and to ensure that the results don't just a bit from
        version to version which would be not noticeable in the short term.

        Parameters:
            experiment_id (UUID): The ID of the experiment.

        Returns:
            Dataframe: The last result for the given experiment ID.
        """
        client = self._object_session.client("s3")
        paginator = client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name, Prefix=f"{experiment_id}/main"
        )
        oldest_object = self._get_oldest_s3_object(page_iterator)

        key = oldest_object["Key"]
        response = client.get_object(Bucket=self.bucket_name, Key=key)
        data = response["Body"].read()
        csv_data = io.StringIO(data.decode("utf-8"))
        return pandas.read_csv(csv_data)
