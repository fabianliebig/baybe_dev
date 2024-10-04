"""This module contains the lookup data for the performance tests.

Attributes:
    LOOKUP_STRUCTURE (Dict[str, DataFrame | Callable]): A dictionary that stores the
    lookup data. The keys represent the names of the lookup tables, and the values can
    be either a DataFrame or a Callable. The DataFrame contains the actual lookup data,
    while the Callable represents a function that generates the lookup data.

"""

from collections.abc import Callable
from pathlib import Path

from pandas import DataFrame, read_csv

from tests.performance_tests.test_cases.data.gen_lookup_functions import (
    create_lookup_for_hartmann,
)

PATH_PREFIX = Path("tests//performance_tests//test_cases//data//lookup_data//")

LOOKUP_STRUCTURE: dict[str, DataFrame | Callable] = {
    "aryl_halides": read_csv(PATH_PREFIX.joinpath("aryl_halides.csv").resolve()),
    "direct_arylation": read_csv(
        PATH_PREFIX.joinpath("direct_arylation.csv").resolve()
    ),
    "cell_media": read_csv(PATH_PREFIX.joinpath("cell_media.csv").resolve()),
    "hartmann_function": create_lookup_for_hartmann(),
}
