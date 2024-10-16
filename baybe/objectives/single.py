"""Functionality for single-target objectives."""

import gc

import pandas as pd
from attrs import define, field
from attrs.validators import instance_of
from typing_extensions import override

from baybe.objectives.base import Objective
from baybe.targets.base import Target
from baybe.utils.dataframe import pretty_print_df
from baybe.utils.plotting import to_string


@define(frozen=True, slots=False)
class SingleTargetObjective(Objective):
    """An objective focusing on a single target."""

    _target: Target = field(validator=instance_of(Target), alias="target")
    """The single target considered by the objective."""

    @override
    def __str__(self) -> str:
        targets_list = [target.summary() for target in self.targets]
        targets_df = pd.DataFrame(targets_list)

        fields = [
            to_string("Type", self.__class__.__name__, single_line=True),
            to_string("Targets", pretty_print_df(targets_df)),
        ]

        return to_string("Objective", *fields)

    @override
    @property
    def targets(self) -> tuple[Target, ...]:
        return (self._target,)

    @override
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        target_data = data[[self._target.name]].copy()
        return self._target.transform(target_data)


# Collect leftover original slotted classes processed by `attrs.define`
gc.collect()
