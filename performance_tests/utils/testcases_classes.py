"""Data classes that are used to define the test cases for the performance tests.

This file contains helper classes which contain all the necessary information to run a
testcase. One interface is defined to execute the in a uniform way and provide the
possibility to evaluate the results of the testcase not only by its return value but
also by other non functional properties like runtime or memory consumption in
future implementations.
"""

import json
from typing import Any
from uuid import UUID

from attrs import define
from pandas import DataFrame


@define
class BenchmarkingResult:
    """A class to store the metadata and the result of a test case."""

    result: DataFrame
    unique_id: UUID
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
        removed_none_metadata["execution_time_nanosec"] = str(self.execution_time_ns)
        return removed_none_metadata

    def to_json(self) -> str:
        """Convert the object to a JSON string."""
        return json.dumps(self.to_s3_dict())
