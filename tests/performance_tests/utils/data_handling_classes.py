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
from sortedcontainers import SortedDict, SortedList

from baybe import __version__
from tests.performance_tests.utils.testcases_classes import (
    MetaDataAndResultPerformanceTest,
)


@define
class ResultPersistenceInterface(ABC):
    """Interface for classes that persist experiment results."""

    @staticmethod
    def _default_baybe_version() -> str:
        return __version__

    date_time: datetime
    baybe_version: str = field(factory=_default_baybe_version)
    """The version of the Baybe library."""

    @abstractmethod
    def persist_new_result(
        self, experiment_id: UUID, result: MetaDataAndResultPerformanceTest
    ) -> None:
        """Persists a new result for the given experiment.

        Args:
            experiment_id: The ID of the experiment.
            result: The result to be persisted.
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
            experiment_id: The ID of the experiment.

        Returns:
            Dataframe: The last result for the given experiment ID.
        """
        pass


@define
class S3ExperimentResultPersistence(ResultPersistenceInterface):
    """Class for persisting experiment results in an S3 bucket."""

    @staticmethod
    def _default_bucket_name() -> str:
        ENVIRONMENT_NOT_SET = "BAYBE_PERFORMANCE_PERSISTANCE_PATH" not in os.environ
        if ENVIRONMENT_NOT_SET:
            raise ValueError(
                "The environment variable "
                "BAYBE_PERFORMANCE_PERSISTANCE_PATH is not set. "
                "A bucket name must be provided."
            )
        return os.environ["BAYBE_PERFORMANCE_PERSISTANCE_PATH"]

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

    @staticmethod
    def _default_repository_owner_org() -> str:
        if "GITHUB_REPOSITORY_OWNER" not in os.environ:
            raise ValueError(
                "The environment variable GITHUB_REPOSITORY_OWNER is not set."
            )
        return os.environ["GITHUB_REPOSITORY_OWNER"]

    @staticmethod
    def _default_actor_initiated_workflow() -> str:
        if "GITHUB_ACTOR" not in os.environ:
            raise ValueError("The environment variable GITHUB_ACTOR is not set.")
        return os.environ["GITHUB_ACTOR"]

    bucket_name: str = field(factory=_default_bucket_name)
    """The name of the S3 bucket where the results are stored."""

    _object_session = boto3.session.Session()
    """The boto3 session object."""

    branch: str = field(factory=_default_branch)
    """The branch of the Baybe library from which the workflow was started."""

    commit_hash: str = field(factory=_default_commit_hash)
    """The commit hash from the last commit where the workflow is started."""

    repository_owner_org: str = field(factory=_default_repository_owner_org)
    """The owner of the repository where the workflow is started. Might be a fork."""

    actor_initiated_workflow: str = field(factory=_default_actor_initiated_workflow)
    """The actor who initiated the workflow. It stays the same for a rerun."""

    _RELEVANT_OWNER_ORG_FOR_SEARCH = "emdgroup"
    """The repository owner organization that is used for fetching results."""

    def persist_new_result(
        self, experiment_id: UUID, result: MetaDataAndResultPerformanceTest
    ) -> None:
        """Persists a new result for the given experiment.

        Args:
            experiment_id: The ID of the experiment.
            result: The result to be persisted.
        """
        client = self._object_session.client("s3")
        bucket_path = (
            f"{self.repository_owner_org}/{experiment_id}/"
            + f"{self.branch}/{self.baybe_version}/"
            + f"{self.date_time.isoformat()}/{self.commit_hash}"
        )

        metadata = result.to_s3_dict()
        metadata["date_time"] = self.date_time.isoformat()
        metadata["workflow_actor"] = self.actor_initiated_workflow

        client.put_object(
            Bucket=self.bucket_name,
            Key=f"{bucket_path}/result.csv",
            Body=result.result.to_csv(),
            ContentType="text/csv",
            Metadata=metadata,
        )

    def _get_newest_s3_object(self, iterator: PageIterator) -> dict:
        """Retrieves the oldest S3 object from the given iterator.

        Args:
            iterator: An iterator that provides access to S3 objects.

        Returns:
            dict: The oldest S3 object as a dictionary.

        Raises:
            ValueError: If no result is found for the given experiment ID.
        """
        latest_object = None
        for page in iterator:
            for content in page["Contents"]:
                OBSERVED_CONTENT_IS_OLDER = (
                    latest_object is not None
                    and content["LastModified"] > latest_object["LastModified"]
                )
                if not latest_object or OBSERVED_CONTENT_IS_OLDER:
                    latest_object = content

        if not latest_object:
            raise ValueError("No result found for the given experiment ID.")
        return latest_object

    def load_compare_result(self, experiment_id: UUID) -> DataFrame:
        """Load the oldest stable result for a given experiment ID.

        Loads the oldest result from an experiment that is created from the main branch
        of the Baybe library. This is done to compare the performance of the library
        over a longer time period and to ensure that the results don't just a bit from
        version to version which would be not noticeable in the short term.

        Parameters:
            experiment_id: The ID of the experiment.

        Returns:
            Dataframe: The last result for the given experiment ID.
        """
        COMPARE_TO_LAST_RELEASE = self.branch == "main"
        if COMPARE_TO_LAST_RELEASE:
            return self._get_newest_dataset_from_last_release(experiment_id)

        return self._get_current_main_newest_result(experiment_id)

    def _get_last_available_release(self, experiment_id: UUID) -> str:
        """Retrieves the last available release for a given experiment ID.

        Parameters:
            experiment_id: The ID of the experiment.

        Returns:
            str: The last available release version.

        Raises:
            ValueError: If the current version has no previous version to compare.
        """
        client = self._object_session.client("s3")
        paginator = client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name,
            Prefix=f"{self._RELEVANT_OWNER_ORG_FOR_SEARCH}/{experiment_id}/main",
        )
        map_of_versions: dict[str, list[str]] = self._extract_baybe_versions(
            page_iterator
        )
        versions = list(map_of_versions.keys())
        compare_version = self._sanitize_baybe_version(self.baybe_version)
        if compare_version not in versions:
            return versions[-1]
        current_index = versions.index(compare_version)
        VERSION_HAS_NO_COMPARATIVE = current_index <= 0
        if VERSION_HAS_NO_COMPARATIVE:
            raise ValueError("The current version has no previous version to compare.")
        return versions[current_index - 1]

    def _extract_baybe_versions(
        self, page_iterator: PageIterator
    ) -> dict[str, list[str]]:
        """Extracts the Baybe versions from the given page iterator.

        Args:
            page_iterator: An iterator that provides pages.

        Returns:
            Dict[str, List[str]]: A dictionary mapping Baybe versions to a set
            of corresponding keys.
        """
        map_of_versions = SortedDict()
        for page in page_iterator:
            if "Contents" in page:
                for key in page["Contents"]:
                    key_str = key["Key"]
                    baybe_version = key_str.split("/")[2]
                    san_baybe_version = self._sanitize_baybe_version(baybe_version)
                    if baybe_version not in map_of_versions:
                        map_of_versions[san_baybe_version] = SortedList()
                    map_of_versions[san_baybe_version].add(key_str)
        return map_of_versions

    def _sanitize_baybe_version(self, baybe_version: str) -> str:
        """Sanitizes the Baybe version by removing any post-release version information.

        Parameters:
          baybe_version: The Baybe version to be sanitized.

        Returns:
        - str: The sanitized Baybe version.
        """
        POST_RELEASE_VERSION = len(baybe_version.split(".")) > 3
        if POST_RELEASE_VERSION:
            baybe_version = ".".join(baybe_version.split(".")[:3])
        return baybe_version

    def _get_newest_dataset_from_last_release(self, experiment_id: UUID) -> DataFrame:
        """Retrieves the newest dataset from the release just before the current one.

        Args:
            experiment_id: The ID of the experiment.

        Returns:
            - DataFrame: The retrieved dataset as a pandas DataFrame.
        """
        client = self._object_session.client("s3")
        paginator = client.get_paginator("list_objects_v2")
        last_available_release = self._get_last_available_release(experiment_id)
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name,
            Prefix=f"{self._RELEVANT_OWNER_ORG_FOR_SEARCH}/{experiment_id}/main/{last_available_release}",
        )
        oldest_object = self._get_newest_s3_object(page_iterator)

        key = oldest_object["Key"]
        return self._retrieve_dataframe_from_s3(key)

    def _retrieve_dataframe_from_s3(self, key: str) -> DataFrame:
        """Retrieves a DataFrame from an S3 bucket.

        Parameters:
            key: The key of the object in the S3 bucket.

        Returns:
            DataFrame: The DataFrame read from the CSV data.
        """
        client = self._object_session.client("s3")
        response = client.get_object(Bucket=self.bucket_name, Key=key)
        data = response["Body"].read()
        csv_data = io.StringIO(data.decode("utf-8"))
        return pandas.read_csv(csv_data)

    def _get_current_main_newest_result(self, experiment_id: UUID) -> DataFrame:
        """Retrieves the newest dataset from the last release for a experiment.

        Args:
            experiment_id: The ID of the experiment.

        Returns:
            The retrieved dataset as a pandas DataFrame.
        """
        client = self._object_session.client("s3")
        paginator = client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name,
            Prefix=f"{self._RELEVANT_OWNER_ORG_FOR_SEARCH}/{experiment_id}/main",
        )
        oldest_object = self._get_newest_s3_object(page_iterator)

        key = oldest_object["Key"]
        return self._retrieve_dataframe_from_s3(key)


@define
class LocalExperimentResultPersistence(ResultPersistenceInterface):
    """Class for persisting experiment results locally."""

    _path: str = "tests/performance_tests/results"

    def __attrs_post_init__(self):
        os.makedirs(self._path, exist_ok=True)

    def persist_new_result(
        self, experiment_id: UUID, result: MetaDataAndResultPerformanceTest
    ) -> None:
        """Persists a new result for the given experiment.

        Args:
            experiment_id: The ID of the experiment.
            result: The result to be persisted.
        """
        result.result.to_csv(
            f"{self._path}/{experiment_id}-{self.date_time.isoformat}-{self.baybe_version}.csv"
        )

    def load_compare_result(self, experiment_id: UUID) -> DataFrame:
        """Load the oldest stable result for a given experiment ID.

        Loads the oldest result from an experiment that is created from the main branch
        of the Baybe library. This is done to compare the performance of the library
        over a longer time period and to ensure that the results don't just a bit from
        version to version which would be not noticeable in the short term.

        Parameters:
            experiment_id: The ID of the experiment.

        Returns:
            Dataframe: The last result for the given experiment ID.
        """
        csv_files = SortedList(
            [
                f
                for f in os.listdir(self._path)
                if f.startswith(str(experiment_id)) and f.endswith(".csv")
            ]
        )
        OLDEST_FILE = csv_files[0]
        return pandas.read_csv(f"{self._path}/{OLDEST_FILE}")
