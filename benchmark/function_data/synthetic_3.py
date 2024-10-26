"""Synthetic dataset. Custom parabolic test with irrelevant parameters."""

from uuid import UUID

from numpy import pi

from baybe.objective import SingleTargetObjective
from baybe.parameters import NumericalContinuousParameter, NumericalDiscreteParameter
from baybe.recommenders import (
    BotorchRecommender,
    RandomRecommender,
    TwoPhaseMetaRecommender,
)
from baybe.targets import NumericalTarget, TargetMode
from benchmark.definition import Benchmark, BenchmarkScenarioConfig
from benchmark.domain.basic import Domain

domain = Domain(
    name="Synthetic dataset with three dimensions.",
    description="""Synthetic dataset.

        Number of Samples            inf
        Dimensionality                 3
        Features:
            x   continuous [-2*pi, 2*pi]
            y   continuous [-2*pi, 2*pi]
            z   discrete {1,2,3,4}
        Targets:
            output   continuous
    Best Value 4.09685
    """,
    parameters=[
        NumericalContinuousParameter("x", (-2 * pi, 2 * pi)),
        NumericalContinuousParameter("y", (-2 * pi, 2 * pi)),
        NumericalDiscreteParameter("z", (1, 2, 3, 4)),
    ],
    objective=SingleTargetObjective(
        target=NumericalTarget(name="output", mode=TargetMode.MAX)
    ),
    lookup="(z==1)* math.sin(x)*(1+math.sin(y)) +(z==2)*(x*math.sin(0.9*x)+math.sin(x)*"
    + "math.sin(y)) +(z==3)*(math.sqrt(x+8)*math.sin(x)+math.sin(x)*math.sin(y))"
    + "+(z==4)*(x*math.sin(1.666*math.sqrt(x+8))+math.sin(x)*math.sin(y))",
)

config = BenchmarkScenarioConfig(
    batch_size=5,
    n_doe_iterations=30,
    n_mc_iterations=50,
    recommender=[
        RandomRecommender(),
        TwoPhaseMetaRecommender(RandomRecommender(), BotorchRecommender(), 1),
    ],
)

benchmark_synthetic_3 = Benchmark(
    benchmark_domain=domain,
    scenario_config=config,
    identifier=UUID("4e131cb7-4de0-4900-b993-1d7d4a194532"),
)
