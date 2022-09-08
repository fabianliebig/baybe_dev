"""
Collection of small utilities
"""
from __future__ import annotations

import ssl
import urllib.request

from functools import partial

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    TYPE_CHECKING,
    Union,
)

import numpy as np
import pandas as pd
import torch
from mordred import Calculator, descriptors
from rdkit import Chem, RDLogger
from rdkit.Chem.AllChem import GetMorganFingerprintAsBitVect
from torch import Tensor

if TYPE_CHECKING:
    from .core import BayBE


def is_valid_smiles(smiles: str) -> bool:
    """
    Test if a SMILES string is valid according to RDKit.

    Parameters
    ----------
    smiles: str
        SMILES string
    Returns
    -------
        bool, True if smiles is valid, False else
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False


def to_tensor(*dfs: pd.DataFrame) -> Union[Tensor, Iterable[Tensor]]:
    """Converts a given set of dataframes into tensors (dropping all indices)."""
    # FIXME This function seems to trigger a problem when some columns in either of the
    #  dfs have a dtype other than int or float (eg object, bool). This can weirdly
    #  happen, even if all values are numeric, eg when a target column is looked up from
    #  a df in simulation, it can have dtype object even if its all floats. As a simple
    #  fix (this seems to be the most reasonable place to take care of this) I changed
    #  df.values to df.values.astype(float), even though this seems like double casting
    #  here
    out = (torch.from_numpy(df.values.astype(float)).to(torch.float32) for df in dfs)
    if len(dfs) == 1:
        out = next(out)
    return out


def check_if_in(element: Any, allowed: list):
    """
    Checks if an element is in a given list of elements and raises a
    context-specific exception if it is not.
    """
    if element not in allowed:
        raise ValueError(
            f"The value '{element}' is not allowed. Must be one of {allowed}."
        )


def name_to_smiles(name: str) -> str:
    """
    Convert from chemical name to SMILES string using chemical identifier resolver.

    Parameters
    ----------
    name : str
        Name or nickname of compound.

    Returns
    ----------
    str
        SMILES string corresponding to chemical name.
    """

    name = name.replace(" ", "%20")

    try:
        url = "http://cactus.nci.nih.gov/chemical/structure/" + name + "/smiles"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # with urlopen(url) as web:
        with urllib.request.urlopen(url, context=ctx) as web:
            smiles = web.read().decode("utf8")

        smiles = str(smiles)
        if "</div>" in smiles:
            return ""

        return smiles
    except Exception:
        return ""


def add_fake_results(
    data: pd.DataFrame,
    obj: BayBE,
    good_reference_values: Optional[Dict[str, list]] = None,
    good_intervals: Optional[List[Tuple[float, float]]] = None,
    bad_intervals: Optional[List[Tuple[float, float]]] = None,
) -> None:
    """
    Add fake results to a dataframe which was the result of the BayBE recommendation
    action. It is possible to identify "good" values, which will be given a better
    target value. With this the algorithm can be driven towards certain optimal values
    whilst still being random. Useful for testing.

    Parameters
    ----------
    data : pandas dataframe
           Output of the recommend function of a BayBE object
    obj : BayBE class instance
          The baybe object which provides configuration, targets, etc.
    good_reference_values : dictionary
                  A dictionaries which defines parameters and respective values
                  which identify what will be considered good values. Conditions for
                  different parameters connected via and logic, ie the entry will only
                  get a good value if all parameters have the good reference values
                  Example {'Param1': [1,4,42], 'Param2': ['A','C']}
    good_intervals : list of 2-tuples
                     Good entries will get a random value in the range defined by this
                     tuple
    bad_intervals : list of 2-tuples
                    Bad entries will get a random value in the range defined by this
                    tuple

    Returns
    -------
    Nothing since it operated directly on the data
    """

    # Sanity checks and standatds for good and bad intervals
    if good_intervals is None:
        good_intervals = []
        for target in obj.targets:
            if target.mode == "MAX":
                interv = (66, 100)
            elif target.mode == "MIN":
                interv = (0, 33)
            elif target.mode == "MATCH":
                lbound = 0 if target.bounds is None else target.bounds[0]
                ubound = 100 if target.bounds is None else target.bounds[1]
                interv = (
                    lbound + 0.2 * (ubound - lbound),
                    lbound + 0.8 * (ubound - lbound),
                )
            else:
                raise ValueError(
                    "Unrecognized target mode when trying to add fake values."
                )
            good_intervals.append(interv)
    if bad_intervals is None:
        bad_intervals = []
        for target in obj.targets:
            if target.mode == "MAX":
                interv = (0, 33)
            elif target.mode == "MIN":
                interv = (66, 100)
            elif target.mode == "MATCH":
                lbound = 0 if target.bounds is None else target.bounds[0]
                ubound = 100 if target.bounds is None else target.bounds[1]
                interv = (
                    ubound + 0.5 * (ubound - lbound),
                    ubound + 2.0 * (ubound - lbound),
                )
            else:
                raise ValueError(
                    "Unrecognized target mode when trying to add fake values."
                )
            bad_intervals.append(interv)

    # Sanity check for reference values of good parameters
    if good_reference_values is None:
        good_reference_values = {}

    for k_target, target in enumerate(obj.targets):
        # add bad values
        data[target.name] = np.random.randint(
            bad_intervals[k_target][0], bad_intervals[k_target][1], len(data)
        )

        # add good values
        masks = []
        if len(good_reference_values) > 0:
            for param, vals in good_reference_values.items():
                if param not in data.columns:
                    raise ValueError(
                        f"When adding fake results you specified good "
                        f"values for the parameter '{param}' but this "
                        f"parameter is not in the dataframe."
                    )
                if not isinstance(vals, list):
                    raise TypeError(
                        f"Entries in parameter good_reference_values "
                        f"(which is a dictionary) must be lists, but you "
                        f"provided {vals}"
                    )
                mask = data[param].apply(partial(lambda x, v: x in v, v=vals))
                masks.append(mask)

            # Good values will be added where the parameters of the
            # corresponding datapoints match the ones defined in good_reference_values
            if len(masks) > 0:
                final_mask = masks[0]
                if len(masks) > 1:
                    for mask in masks[1:]:
                        final_mask &= mask

                data.loc[final_mask, target.name] = np.random.randint(
                    good_intervals[k_target][0],
                    good_intervals[k_target][1],
                    final_mask.sum(),
                )


def add_parameter_noise(
    data: pd.DataFrame,
    obj: BayBE,
    noise_type: str = "absolute",
    noise_level: float = 1.0,
) -> None:
    """
    Adds uniform noise to parameter values of a recommendation frame. Simulates
    experimental noise and inputting numerical values that are slightly different
    than the recommendations coming from the search space.

    Parameters
    ----------
    data : pandas dataframe
           output of the recommend function of a BayBE object
    obj : BayBE class instance
          the baybe object which provides configuration, targets, etc.
    noise_type : str
        Defines whether the noise should be additive
    noise_level : float
        Level/magnitude of the noise, numerical value for type absolute and percentage
        for type relative_percent

    Returns
    -------
        Nothing
    """
    for param in obj.parameters:
        if "NUM" in param.type:
            if noise_type == "relative_percent":
                data[param.name] *= np.random.uniform(
                    1.0 - noise_level / 100.0, 1.0 + noise_level / 100.0, len(data)
                )
            elif noise_type == "absolute":
                data[param.name] += np.random.uniform(
                    -noise_level, noise_level, len(data)
                )
            else:
                raise ValueError(
                    f"Parameter noise_type was {noise_type} but must be either "
                    f'"absolute" or "relative_percent"'
                )


def smiles_to_mordred_features(
    smiles_list: list, prefix: str = "", dropna: bool = True
) -> pd.DataFrame:
    """
    Compute Mordred chemical descriptors for a list of SMILES strings.

    Parameters
    ----------
    smiles_list : list
        List of SMILES strings.
    prefix : str
        Name prefix for each descriptor (e.g., nBase --> name_nBase).
    dropna : bool
        If true, drop columns which contain np.NaNs.

    Returns
    ----------
    pandas.DataFrame
        DataFrame containing overlapping Mordred descriptors for each SMILES
        string.
    """
    calc = Calculator(descriptors)

    output = []
    for smiles in smiles_list:
        try:
            data_i = calc(Chem.MolFromSmiles(smiles)).fill_missing()
        except Exception:
            data_i = np.full(len(calc.descriptors), np.NaN)

        output.append(list(data_i))

    descriptor_names = list(calc.descriptors)
    columns = []
    for entry in descriptor_names:
        columns.append(prefix + str(entry))

    dataframe = pd.DataFrame(data=output, columns=columns)

    if dropna:
        dataframe = dataframe.dropna(axis=1)

    return dataframe


def smiles_to_rdkit_features(
    smiles_list: list, prefix: str = "", dropna: bool = True
) -> pd.DataFrame:
    """
    Compute RDKit chemical descriptors for a list of SMILES strings.

    Parameters
    ----------
    smiles_list : list
        List of SMILES strings.
    prefix : str
        Name prefix for each descriptor (e.g., nBase --> name_nBase).
    dropna : bool
        If true, drop columns which contain np.NaNs.

    Returns
    ----------
    pandas.DataFrame
        DataFrame containing overlapping RDKit descriptors for each SMILES
        string.
    """

    mols = []
    for smiles in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError(
                    f"The smiles {smiles} does not seem " f"to chemically valid"
                )
            mols.append(mol)
        except Exception as ex:
            raise ValueError(
                f"The smiles {smiles} does not seem " f"to chemically valid"
            ) from ex

    res = []
    for mol in mols:
        desc = {prefix + dname: func(mol) for dname, func in Chem.Descriptors.descList}
        res.append(desc)

    df = pd.DataFrame(res)
    if dropna:
        df = df.dropna(axis=1)

    return df


def smiles_to_fp_features(
    smiles_list: list,
    prefix: str = "",
    dtype: Union[Type[int], Type[float]] = int,
    radius: int = 4,
    n_bits: int = 1024,
) -> pd.DataFrame:
    """
    Compute standard morgan molecule fingerprints for a list of SMILES strings.

    Parameters
    ----------
    smiles_list : list
        List of SMILES strings.
    prefix : str
        Name prefix for each descriptor (e.g., nBase --> name_nBase).
    dtype : datatype int or float
        Specifies whether fingerprints will have int or float datatype
    radius : int
        Radius for the Morgan Fingerprint
    n_bits : int
        Number of bits for the Morgan fingerprint

    Returns
    ----------
    pandas.DataFrame
        DataFrame containing Morgan fingerprints for each SMILES string.
    """

    mols = []
    for smiles in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError(
                    f"The smiles {smiles} does not seem " f"to chemically valid"
                )
            mols.append(mol)
        except Exception as ex:
            raise ValueError(
                f"The smiles {smiles} does not seem " f"to chemically valid"
            ) from ex

    res = []
    for mol in mols:
        RDLogger.logger().setLevel(RDLogger.CRITICAL)

        fingerp = GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits).ToBitString()
        fingerp = map(int, fingerp)
        fpvec = np.array(list(fingerp))
        res.append(
            {prefix + "FP" + f"{k + 1}": dtype(bit) for k, bit in enumerate(fpvec)}
        )

    df = pd.DataFrame(res)

    return df


def df_drop_single_value_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop dataframe columns with zero variance. Adapted from edbo.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to be cleaned
    Returns
    -------
    pandas.DataFrame
        A new dataframe
    """
    to_keep = []
    for k in range(len(df.columns)):
        if len(df.iloc[:, k].drop_duplicates()) > 1:
            to_keep.append(df.columns.values[k])

    return df[to_keep]


def df_drop_string_columns(
    df: pd.DataFrame, ignore_list: Optional[list] = None
) -> pd.DataFrame:
    """
    Drop dataframe columns with non-numeric values. Adapted from edbo.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to be cleaned
    ignore_list : list
        List of columns that should not be dropped, even if they include strings
    Returns
    -------
    pandas.DataFrame
        A new dataframe
    """
    ignore_list = ignore_list or []

    to_keep = []
    for k in range(len(df.columns)):
        unique = df.iloc[:, k].drop_duplicates()
        keep_q = True
        for j in range(len(unique)):
            if isinstance(unique.iloc[j], str):
                keep_q = False
                break
        if keep_q:
            to_keep.append(df.columns.values[k])

    return df[to_keep + ignore_list]


def df_uncorrelated_features(
    df: pd.DataFrame, exclude_list: Optional[List[str]] = None, threshold: float = 0.7
):
    """
    Returns an uncorrelated set of features. Adapted from edbo.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to be cleaned
    exclude_list : list of strings or None
        If provided this defines the columns that should be ignored
    threshold : float
        Threshold for column-column correlation above which columns should be dropped
    Returns
    -------
    data : pandas.DataFrame
        A new dataframe
    """

    if exclude_list is None:
        data = df.copy()
    else:
        data = df.drop(columns=exclude_list)

    corr = data.corr().abs()
    to_keep = []
    for i in range(len(corr.iloc[:, 0])):
        above = corr.iloc[:i, i]
        if len(to_keep) > 0:
            above = above[to_keep]
        if len(above[above < threshold]) == len(above):
            to_keep.append(corr.columns.values[i])

    data = data[to_keep]

    if exclude_list is not None:
        data[exclude_list] = df.loc[:, exclude_list]

    return data


class StrictValidationError(Exception):
    """
    This class is used as a workaround that can be used to stop pydantic from continuing
    validating other members when the validation of a specific field fails.

    The issue is described here:
    https://github.com/pydantic/pydantic/issues/3915
    """


def geom_mean(x: np.ndarray, weights):
    """
    Calculate geometric mean. Own implementation instead of gmean from scistats due to
    avoiding logarithm and division errors
    """
    # pylint: disable=invalid-name
    res = 1.0

    for k in range(x.shape[1]):
        res *= x[:, k] ** (weights[k] / np.sum(weights))

    return res