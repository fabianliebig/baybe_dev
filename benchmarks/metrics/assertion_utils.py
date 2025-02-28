"""This module is for forming patterns to assert results."""

from abc import ABC
from enum import Enum
from typing import Any, Protocol

from attrs import define, field
from attrs.validators import deep_iterable, instance_of
from pandas import DataFrame
from scipy.stats import wilcoxon

from benchmarks.metrics.base import Metric


class ComparisonOperator(Enum):
    """Enum class for comparison operators."""

    EQUAL = "=="
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="


@define
class TwoSidePatternItem(Protocol):
    """Interface for a pattern item with two sides."""

    def check(self, predecessor_result: DataFrame, current_result: DataFrame) -> bool:
        """Check the pattern.

        Args:
            predecessor_result: The result of the predecessor benchmark execution.
            current_result: The result of the current benchmark execution.
        """


@define
class OneSidePatternItem(Protocol):
    """Interface for a pattern item with two sides."""

    def check(self, current_result: DataFrame) -> bool:
        """Check the pattern.

        Args:
            predecessor_result: The result of the predecessor benchmark execution.
            current_result: The result of the current benchmark execution.
        """


@define
class PatternItem(ABC):
    """Class for a pattern item."""

    metric: Metric = field(validator=instance_of(Metric))
    """The metric to be used for the pattern."""

    comparison_operator: ComparisonOperator = field(
        validator=instance_of(ComparisonOperator)
    )
    """The comparison operator to be used for the pattern."""

    def _compare_values(self, value1: float, value2: float) -> bool:
        """Compare the values according to the comparison operator."""
        if self.comparison_operator == ComparisonOperator.EQUAL:
            return value1 == value2
        elif self.comparison_operator == ComparisonOperator.GREATER:
            return value1 > value2
        elif self.comparison_operator == ComparisonOperator.LESS:
            return value1 < value2
        elif self.comparison_operator == ComparisonOperator.GREATER_EQUAL:
            return value1 >= value2
        elif self.comparison_operator == ComparisonOperator.LESS_EQUAL:
            return value1 <= value2
        else:
            raise ValueError("Invalid comparison operator.")


@define
class PatternItemRatioThreshold(PatternItem, TwoSidePatternItem):
    """Class for a pattern item with ratio threshold."""

    ratio_threshold: float = field(validator=instance_of(float))
    """The ratio threshold for the pattern.
    The ratio will always be on the right side of the comparison operator."""

    def check(self, predecessor_result: DataFrame, current_result: DataFrame) -> bool:
        """Check the pattern.

        Args:
            predecessor_result: The result of the predecessor benchmark execution.
            current_result: The result of the current benchmark execution.
        """
        predecessor_metric = self.metric.calculate(predecessor_result)
        current_metric = self.metric.calculate(current_result)
        ratio = current_metric / predecessor_metric
        return self._compare_values(ratio, self.ratio_threshold)


@define
class PatternItemValueThreshold(PatternItem, OneSidePatternItem):
    """Class for a pattern item with absolute value threshold."""

    value_threshold: float = field(validator=instance_of(float))
    """The value threshold for the pattern."""

    def check(self, current_result: DataFrame) -> bool:
        """Check the pattern.

        Args:
            predecessor_result: The result of the predecessor benchmark execution.
            current_result: The result of the current benchmark execution.
        """
        current_metric = self.metric.calculate(current_result)
        return self._compare_values(current_metric, self.value_threshold)


@define
class PatternItemPureMetricComparison(PatternItem, TwoSidePatternItem):
    """Class for a pattern item with pure metric comparison."""

    def check(self, predecessor_result: DataFrame, current_result: DataFrame) -> bool:
        """Check the pattern.

        Args:
            predecessor_result: The result of the predecessor benchmark execution.
            current_result: The result of the current benchmark execution.
        """
        predecessor_metric = self.metric.calculate(predecessor_result)
        current_metric = self.metric.calculate(current_result)
        return self._compare_values(current_metric, predecessor_metric)


@define
class PatternBasedAssertion:
    """Class for checking statistical significance and assert boolean patterns."""

    predecessor_result: DataFrame = field(validator=instance_of(DataFrame))
    """The result of the predecessor benchmark execution."""

    current_result: DataFrame = field(validator=instance_of(DataFrame))
    """The result of the current benchmark execution."""

    significance_level: float = field(validator=instance_of(float))
    """The significance level for the statistical test where the pattern will be
    checked if the variation is significant."""

    metrics: list[PatternItem] = field(
        validator=deep_iterable(instance_of(PatternItem))
    )
    """The list of pattern items to be checked."""

    statistical_test = field(default=wilcoxon)
    """The statistical test to be used for checking the significance of the pattern.
    The first two arguments of the function must be the two samples to be compared.
    The default is Wilcoxon signed-rank test."""

    def pattern_apply(self) -> bool:
        """Check significance and assert patterns."""
        p_value = self.statistical_test(
            self.predecessor_result, self.current_result
        ).pvalue
        if p_value > self.significance_level:
            return False
        for metric in self.metrics:
            if not metric.check(self.predecessor_result, self.current_result):
                return False
        return True
