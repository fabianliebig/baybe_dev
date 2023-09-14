"""Tests for the substance parameter."""

import pytest

from baybe.utils.chemistry import _MORDRED_INSTALLED, _RDKIT_INSTALLED
from baybe.utils.dataframe import add_fake_results, add_parameter_noise

_CHEM_INSTALLED = _MORDRED_INSTALLED and _RDKIT_INSTALLED
if _CHEM_INSTALLED:
    from baybe.parameters import SUBSTANCE_ENCODINGS


if _CHEM_INSTALLED:

    @pytest.mark.parametrize(
        "parameter_names",
        [["Categorical_1", f"Substance_1_{enc}"] for enc in SUBSTANCE_ENCODINGS],
        ids=SUBSTANCE_ENCODINGS,
    )
    def test_run_iterations(baybe, batch_quantity, n_iterations):
        """Test running some iterations with fake results and a substance parameter."""
        for k in range(n_iterations):
            rec = baybe.recommend(batch_quantity=batch_quantity)

            add_fake_results(rec, baybe)
            if k % 2:
                add_parameter_noise(rec, baybe.parameters, noise_level=0.1)

            baybe.add_measurements(rec)
