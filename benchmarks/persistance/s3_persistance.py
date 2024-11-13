"""Classes for persisting and loading experiment results to a S3-Bucket."""

import json
import os

import boto3
import boto3.session
from attr import define, field
from attrs.validators import instance_of
from git import Repo

from benchmarks import Benchmark, Result


@define
class S3ExperimentResultPersistence:
    """Class for persisting experiment results in an S3 bucket."""

    _bucket_name: str = field(validator=instance_of(str), init=False)
    """The name of the S3 bucket where the results are stored."""

    _object_session = boto3.session.Session()
    """The boto3 session object. This will load the respective credentials
    from the environment variables within the conatiner."""

    _branch: str = field(validator=instance_of(str), init=False)
    """The branch of the Baybe library from which the workflow was started."""

    _workflow_run_id: str = field(validator=instance_of(str), init=False)
    """The ID of the workflow run."""

    @_bucket_name.default
    def _default_bucket_name(self) -> str:
        ENVIRONMENT_NOT_SET = "BAYBE_PERFORMANCE_PERSISTANCE_PATH" not in os.environ
        if ENVIRONMENT_NOT_SET:
            raise ValueError(
                "The environment variable "
                "BAYBE_PERFORMANCE_PERSISTANCE_PATH is not set. "
                "A bucket name must be provided."
            )
        return os.environ["BAYBE_PERFORMANCE_PERSISTANCE_PATH"]

    @_branch.default
    def _default_branch(self) -> str:
        repo = Repo(search_parent_directories=True)
        current_branch = repo.active_branch.name
        sanitized_branch = current_branch.replace("/", "-")
        return sanitized_branch

    @_workflow_run_id.default
    def _default_workflow_id(self) -> str:
        if "GITHUB_RUN_ID" not in os.environ:
            raise ValueError("The environment variable GITHUB_RUN_ID is not set.")
        return os.environ["GITHUB_RUN_ID"]

    def persist_new_result(self, result: Result, benchmark: Benchmark) -> None:
        """Store the result of a performance test.

        This method will store the result of a performance test in an S3 bucket.
        The key of the object will be the experiment ID, the branch, the baybe-version,
        the start datetime, the commit hash and the workflow run ID.

        Args:
            result: The result to be persisted.
            benchmark: The benchmark definition that produced the result.
        """
        experiment_id = result.benchmark_identifier
        metadata = result.metadata
        client = self._object_session.client("s3")
        bucket_path_key = (
            f"{experiment_id}/{self._branch}/{metadata.latest_baybe_tag}/"
            + f"{metadata.start_datetime.isoformat()}/"
            + f"{metadata.commit_hash}/{self._workflow_run_id}"
        )
        result_dict = result.to_dict()
        result_dict["best_possible_result"] = benchmark.best_possible_result
        result_dict["settings"] = benchmark.settings.to_dict()
        result_dict["optimal_function_inputs"] = benchmark.optimal_function_inputs
        result_dict["description"] = benchmark.description
        client.put_object(
            Bucket=self._bucket_name,
            Key=f"{bucket_path_key}/result.json",
            Body=json.dumps(result_dict),
            ContentType="application/json",
        )
