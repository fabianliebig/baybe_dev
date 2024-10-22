"""Base classes for the benchmarking results."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from attrs import define, field


@define(frozen=True)
class Result(ABC):
    """Abstract base class for all benchmarking results."""

    @staticmethod
    def _convert_metadata_to_string(metadata: dict[Any, Any]) -> dict[str, str]:
        """Convert the metadata to a string representation.

        The function will convert the metadata to a string representation
        to ensure that the metadata can be written to a csv file.
        """
        metadata_return: dict[str, str] = dict()
        for key, value in metadata.items():
            sanitized_key = str(key).replace(" ", "_")
            metadata_return[sanitized_key] = str(value)
        return metadata_return

    title: str
    """The title of the benchmarking result."""

    identifier: UUID
    """The unique identifier of the benchmark running which can be set
    to compare different executions of the same benchmark setting."""

    metadata: dict[str, str] = field(converter=_convert_metadata_to_string)
    """Metadata about the benchmarking result."""

    @abstractmethod
    def get_execution_time_ns(self) -> float:
        """Return the execution time of the benchmark in nanoseconds."""
        pass
