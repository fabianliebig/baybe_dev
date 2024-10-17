"""Performance tests for the baybe package."""

from datetime import datetime
from pathlib import Path
from uuid import UUID

from pandas import DataFrame, read_csv

from baybe.campaign import Campaign
from baybe.objective import SingleTargetObjective
from baybe.parameters import (
    SubstanceEncoding,
    SubstanceParameter,
)
from baybe.recommenders.pure.nonpredictive.sampling import RandomRecommender
from baybe.searchspace import SearchSpace
from baybe.simulation import simulate_scenarios
from baybe.targets import NumericalTarget, TargetMode
from benchmark import (
    NormalizedNegativeRootMeanSquaredErrorMetric,
    SingleExecutionBenchmark,
)
from benchmark.persistance import S3ExperimentResultPersistence

PATH_PREFIX = Path(".//")


def test_case_aryl_halides() -> DataFrame:
    """Test case 1."""
    aryl_halides_mordred = [
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
    ]

    objective = SingleTargetObjective(
        target=NumericalTarget(name="yield", mode=TargetMode.MAX)
    )

    campaign = Campaign(
        searchspace=SearchSpace.from_product(parameters=aryl_halides_mordred),
        objective=objective,
    )
    campaign_rand = Campaign(
        searchspace=SearchSpace.from_product(parameters=aryl_halides_mordred),
        recommender=RandomRecommender(),
        objective=objective,
    )
    lookup_aryl_halides = read_csv(PATH_PREFIX.joinpath("aryl_halides.csv").resolve())
    batch_size = 2
    n_doe_iterations = 40
    n_mc_iterations = 200

    scenarios = {"Mordred Encoding": campaign, "Random Baseline": campaign_rand}
    return simulate_scenarios(
        scenarios,
        lookup_aryl_halides,
        batch_size=batch_size,
        n_doe_iterations=n_doe_iterations,
        n_mc_iterations=n_mc_iterations,
        impute_mode="ignore",
    )


if __name__ == "__main__":
    title = "Aryl Halides Simulation maximum yield with Mordred"
    unique_id = UUID("23df40f6-243c-49ca-ae71-81d733d8a88d")
    metadata = {
        "DOE iterations": "40",
        "batch size": "2",
        "n_mc_iterations": "200",
        "title": title,
        "impute_mode": "ignore"
    }
    lookup_aryl_halides = read_csv(PATH_PREFIX.joinpath("aryl_halides.csv").resolve())

    metric = NormalizedNegativeRootMeanSquaredErrorMetric(
        lookup=lookup_aryl_halides,
        objective_name="yield",
        target_mode_to_eval=TargetMode.MAX,
    )
    benchmark = SingleExecutionBenchmark(
        title=title,
        identifier=unique_id,
        benchmark_function=test_case_aryl_halides,
        metadata=metadata,
        metrics=[metric],
    )
    result = benchmark.execute_benchmark()
    persister = S3ExperimentResultPersistence(
        datetime.now(), branch="main", baybe_version="0.1.0"
    )
    persister.persist_new_result(result)
