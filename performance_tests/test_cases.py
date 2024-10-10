"""Test cases for performance tests."""

from collections.abc import Callable, Sequence
from uuid import UUID

from pandas import DataFrame

ReturnValue = tuple[DataFrame, UUID, dict[str, str]]
CallableType = Callable[[], ReturnValue]


def test_case_1() -> ReturnValue:
    """Test case 1."""
    return DataFrame(), UUID("c6f4f3a5-0b7d-4e5a-9a2f-4b2b2b2b2b2b"), {"test": "test"}


PERFORMANCE_TEST_CALLABLES: Sequence[CallableType] = [test_case_1]
