"""This module contains a sequence of Parameter objects called `PARAMETER_COMBINATION`.

Each `Parameter` object represents a specific combination of
parameters for a performance test.
"""

from typing import Dict, Sequence

from baybe.parameters import (
    CategoricalEncoding,
    CategoricalParameter,
    NumericalContinuousParameter,
    NumericalDiscreteParameter,
    SubstanceEncoding,
    SubstanceParameter,
)
from baybe.parameters.base import Parameter
from tests.performance_tests.test_cases.gen_parameter_helper_functions import (
    hartmann_parameters,
)

PARAMETER_COMBINATION: Dict[str, Sequence[Parameter]] = {
    "aryl_halides_mordred": [
        SubstanceParameter(
            name="base",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "BTMG": "CN(C)/C(N(C)C)=N\\C(C)(C)C",
                "MTBD": "CN1CCCN2CCCN=C12",
                "P2Et": "CN(C)P(N(C)C)(N(C)C)=NP(N(C)C)(N(C)C)=NCC",
            },
        ),
        SubstanceParameter(
            name="ligand",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "XPhos": "CC(C)C1=CC(C(C)C)=CC(C(C)C)=C1C2=C(P(C3"
                "CCCCC3)C4CCCCC4)C=CC=C2",
                "t-BuXPhos": "CC(C)C(C=C(C(C)C)C=C1C(C)C)=C1C2=CC=CC=C2P(C(C)"
                "(C)C)C(C)(C)C",
                "t-BuBrettPhos": "CC(C)C1=CC(C(C)C)=CC(C(C)C)=C1C2=C(P(C(C)(C)C)C(C)"
                "(C)C)C(OC)=CC=C2OC",
                "AdBrettPhos": "CC(C1=C(C2=C(OC)C=CC(OC)=C2P(C34CC5CC(C4)CC(C5)C3)C67"
                "CC8CC(C7)CC(C8)C6)C(C(C)C)=CC(C(C)C)=C1)C",
            },
        ),
        SubstanceParameter(
            name="additive",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "3,5-dimethylisoxazole": "Cc1onc(C)c1",
                "3-methyl-5-phenylisoxazole": "Cc1cc(on1)c2ccccc2",
                "3-methylisoxazole": "Cc1ccon1",
                "3-phenylisoxazole": "o1ccc(n1)c2ccccc2",
                "4-phenylisoxazole": "o1cc(cn1)c2ccccc2",
                "5-(2,6-difluorophenyl)isoxazole": "Fc1cccc(F)c1c2oncc2",
                "5-Phenyl-1,2,4-oxadiazole": "c1ccc(-c2ncno2)cc1",
                "5-methyl-3-(1H-pyrrol-1-yl)isoxazole": "Cc1onc(c1)n2cccc2",
                "5-methylisoxazole": "Cc1oncc1",
                "5-phenylisoxazole": "o1nccc1c2ccccc2",
                "N,N-dibenzylisoxazol-3-amine": "C(N(Cc1ccccc1)c2ccon2)c3ccccc3",
                "N,N-dibenzylisoxazol-5-amine": "C(N(Cc1ccccc1)c2oncc2)c3ccccc3",
                "benzo[c]isoxazole": "o1cc2ccccc2n1",
                "benzo[d]isoxazole": "o1ncc2ccccc12",
                "ethyl-3-methoxyisoxazole-5-carboxylate": "CCOC(=O)c1onc(OC)c1",
                "ethyl-3-methylisoxazole-5-carboxylate": "CCOC(=O)c1onc(C)c1",
                "ethyl-5-methylisoxazole-3-carboxylate": "CCOC(=O)c1cc(C)on1",
                "ethyl-5-methylisoxazole-4-carboxylate": "CCOC(=O)c1cnoc1C",
                "ethyl-isoxazole-3-carboxylate": "CCOC(=O)c1ccon1",
                "ethyl-isoxazole-4-carboxylate": "CCOC(=O)c1conc1",
                "methyl-5-(furan-2-yl)isoxazole-3-carboxylate": "COC(=O)c1cc(o"
                "n1)c2occc2",
                "methyl-5-(thiophen-2-yl)isoxazole-3-carboxylate": "COC(=O)c1c"
                "c(on1)c2sccc2",
                "methyl-isoxazole-5-carboxylate": "COC(=O)c1oncc1",
            },
        ),
        SubstanceParameter(
            name="aryl_halide",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "1-bromo-4-(trifluoromethyl)benzene": "FC(F)(F)c1ccc(Br)cc1",
                "1-bromo-4-ethylbenzene": "CCc1ccc(Br)cc1",
                "1-bromo-4-methoxybenzene": "COc1ccc(Br)cc1",
                "1-chloro-4-(trifluoromethyl)benzene": "FC(F)(F)c1ccc(Cl)cc1",
                "1-chloro-4-ethylbenzene": "CCc1ccc(Cl)cc1",
                "1-chloro-4-methoxybenzene": "COc1ccc(Cl)cc1",
                "1-ethyl-4-iodobenzene": "CCc1ccc(I)cc1",
                "1-iodo-4-(trifluoromethyl)benzene": "FC(F)(F)c1ccc(I)cc1",
                "1-iodo-4-methoxybenzene": "COc1ccc(I)cc1",
                "2-bromopyridine": "Brc1ccccn1",
                "2-chloropyridine": "Clc1ccccn1",
                "2-iodopyridine": "Ic1ccccn1",
                "3-bromopyridine": "Brc1cccnc1",
                "3-chloropyridine": "Clc1cccnc1",
                "3-iodopyridine": "Ic1cccnc1",
            },
        ),
    ],
    "cell_media": [
        NumericalContinuousParameter(name="param_1", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_2", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_3", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_4", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_5", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_6", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_7", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_8", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_9", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_10", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_11", bounds=(0, 1)),
        NumericalContinuousParameter(name="param_12", bounds=(0, 1)),
        CategoricalParameter(
            name="cell_line",
            encoding=CategoricalEncoding.OHE,
            values=(
                "P1 13E4 qP",
                "P2 13E7 qP",
                "P3 13F1 qP",
                "P4 13G10 qP",
                "P5 15-4 qP",
                "P6 15-5 qP",
                "P7 18-9 qP",
                "P8 18-15 qP",
                "P9 18-17 qP",
                "P10 23B6 qP",
                "P1 2F4",
                "P2 2F5",
                "P3 15-5",
                "P4 CHO-S",
                "P5 DG44",
                "P6 DuxB11",
                "P1 23 qP",
                "P2 3A6 qP",
                "P3 15-5 qP",
                "P4 NIST 92-6 qP",
                "P5 NIST 118-28 qP",
                "P6 EPO Fc 33 qP",
                "P7 EPO Fc 10 qP",
                "P8 41-2 qP",
                "P9 SP5 qP",
            ),
        ),
    ],
    "hartmann_function": hartmann_parameters(),
    "direct_arylation_mordred": [
        SubstanceParameter(
            name="Base",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "Potassium acetate": "O=C([O-])C.[K+]",
                "Potassium pivalate": "O=C([O-])C(C)(C)C.[K+]",
                "Cesium acetate": "O=C([O-])C.[Cs+]",
                "Cesium pivalate": "O=C([O-])C(C)(C)C.[Cs+]",
            },
        ),
        SubstanceParameter(
            name="Ligand",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "BrettPhos": "CC(C)C1=CC(C(C)C)=C(C(C(C)C)=C1)C2=C(P(C3CCCCC3)"
                "C4CCCCC4)C(OC)=CC=C2OC",
                "Di-tert-butylphenylphosphine": "CC(C)(C)P(C1=CC=CC=C1)C(C)(C)C",
                "(t-Bu)PhCPhos": "CN(C)C1=CC=CC(N(C)C)=C1C2=CC=CC=C2P"
                "(C(C)(C)C)C3=CC=CC=C3",
                "Tricyclohexylphosphine": "P(C1CCCCC1)(C2CCCCC2)C3CCCCC3",
                "PPh3": "P(C1=CC=CC=C1)(C2=CC=CC=C2)C3=CC=CC=C3",
                "XPhos": "CC(C1=C(C2=CC=CC=C2P(C3CCCCC3)C4CCCCC4)C(C"
                "(C)C)=CC(C(C)C)=C1)C",
                "P(2-furyl)3": "P(C1=CC=CO1)(C2=CC=CO2)C3=CC=CO3",
                "Methyldiphenylphosphine": "CP(C1=CC=CC=C1)C2=CC=CC=C2",
                "1268824-69-6": "CC(OC1=C(P(C2CCCCC2)C3CCCCC3)C(OC(C)C)=CC=C1)C",
                "JackiePhos": "FC(F)(F)C1=CC(P(C2=C(C3=C(C(C)C)C=C(C(C)"
                "C)C=C3C(C)C)C(OC)=CC=C2OC)C4=CC(C(F)(F)F)=CC(C(F)(F)F)=C4)=CC(C(F)(F)F)=C1",
                "SCHEMBL15068049": "C[C@]1(O2)O[C@](C[C@]2(C)P3C4=CC=C"
                "C=C4)(C)O[C@]3(C)C1",
                "Me2PPh": "CP(C)C1=CC=CC=C1",
            },
        ),
        SubstanceParameter(
            name="Solvent",
            encoding=SubstanceEncoding.MORDRED,
            data={
                "DMAc": "CC(N(C)C)=O",
                "Butyornitrile": "CCCC#N",
                "Butyl Ester": "CCCCOC(C)=O",
                "p-Xylene": "CC1=CC=C(C)C=C1",
            },
        ),
        NumericalDiscreteParameter(name="Concentration", values=(0.057, 0.1, 0.153)),
        NumericalDiscreteParameter(name="Temp_C", values=(90, 105, 120)),
    ],
    "direct_arylation_rdkit": [
        SubstanceParameter(
            name="Base",
            encoding=SubstanceEncoding.RDKIT,
            data={
                "Potassium acetate": "O=C([O-])C.[K+]",
                "Potassium pivalate": "O=C([O-])C(C)(C)C.[K+]",
                "Cesium acetate": "O=C([O-])C.[Cs+]",
                "Cesium pivalate": "O=C([O-])C(C)(C)C.[Cs+]",
            },
        ),
        SubstanceParameter(
            name="Ligand",
            encoding=SubstanceEncoding.RDKIT,
            data={
                "BrettPhos": "CC(C)C1=CC(C(C)C)=C(C(C(C)C)=C1)C2=C(P(C3CCCCC3)"
                "C4CCCCC4)C(OC)=CC=C2OC",
                "Di-tert-butylphenylphosphine": "CC(C)(C)P(C1=CC=CC=C1)C(C)(C)C",
                "(t-Bu)PhCPhos": "CN(C)C1=CC=CC(N(C)C)=C1C2=CC=CC=C2P"
                "(C(C)(C)C)C3=CC=CC=C3",
                "Tricyclohexylphosphine": "P(C1CCCCC1)(C2CCCCC2)C3CCCCC3",
                "PPh3": "P(C1=CC=CC=C1)(C2=CC=CC=C2)C3=CC=CC=C3",
                "XPhos": "CC(C1=C(C2=CC=CC=C2P(C3CCCCC3)C4CCCCC4)C(C"
                "(C)C)=CC(C(C)C)=C1)C",
                "P(2-furyl)3": "P(C1=CC=CO1)(C2=CC=CO2)C3=CC=CO3",
                "Methyldiphenylphosphine": "CP(C1=CC=CC=C1)C2=CC=CC=C2",
                "1268824-69-6": "CC(OC1=C(P(C2CCCCC2)C3CCCCC3)C(OC(C)C)=CC=C1)C",
                "JackiePhos": "FC(F)(F)C1=CC(P(C2=C(C3=C(C(C)C)C=C(C(C)"
                "C)C=C3C(C)C)C(OC)=CC=C2OC)C4=CC(C(F)(F)F)=CC(C(F)(F)F)=C4)=CC(C(F)(F)F)=C1",
                "SCHEMBL15068049": "C[C@]1(O2)O[C@](C[C@]2(C)P3C4=CC=C"
                "C=C4)(C)O[C@]3(C)C1",
                "Me2PPh": "CP(C)C1=CC=CC=C1",
            },
        ),
        SubstanceParameter(
            name="Solvent",
            encoding=SubstanceEncoding.RDKIT,
            data={
                "DMAc": "CC(N(C)C)=O",
                "Butyornitrile": "CCCC#N",
                "Butyl Ester": "CCCCOC(C)=O",
                "p-Xylene": "CC1=CC=C(C)C=C1",
            },
        ),
        NumericalDiscreteParameter(name="Concentration", values=(0.057, 0.1, 0.153)),
        NumericalDiscreteParameter(name="Temp_C", values=(90, 105, 120)),
    ],
}
