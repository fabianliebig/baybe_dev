"""This module contains the lookup data for the performance tests.

Attributes:
    LOOKUP_STRUCTURE (Dict[str, DataFrame | Callable]): A dictionary that stores the
    lookup data. The keys represent the names of the lookup tables, and the values can
    be either a DataFrame or a Callable. The DataFrame contains the actual lookup data,
    while the Callable represents a function that generates the lookup data.

"""

from typing import Callable, Dict, Union

from pandas import DataFrame, read_csv

LOOKUP_STRUCTURE: Dict[str, Union[DataFrame, Callable]] = {
    "aryl_halides": read_csv(
        "tests//performance_tests//testcases/lookup_data//aryl_halides.csv"
    ),
    "direct_arylation": read_csv(
        "tests//performance_tests//testcases/lookup_data//direct_arylation.csv"
    ),
}
