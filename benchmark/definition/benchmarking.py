"""Definition of the Benchmark class."""

import time
from datetime import datetime
from uuid import UUID, uuid4

from attrs import define, field
from attrs.validators import instance_of

from baybe.campaign import Campaign
from baybe.searchspace import SearchSpace
from baybe.simulation import simulate_scenarios
from benchmark.definition.config import BenchmarkScenarioConfig
from benchmark.domain.basic import Domain
from benchmark.result.result import Result


@define
class Benchmark:
    """A class to define a benchmark task."""

    benchmark_domain: Domain = field(validator=instance_of(Domain))
    """The domain of the benchmark including
    the name, a description and further data to run the benchmark."""

    scenario_config: BenchmarkScenarioConfig = field(
        validator=instance_of(BenchmarkScenarioConfig)
    )
    """The configuration of the benchmark scenario."""

    identifier: UUID = field(factory=uuid4, validator=instance_of(UUID))
    """The unique identifier of the benchmark running which can be set
    to compare different executions of the same benchmark setting."""

    def run(self) -> Result:
        """Execute the benchmark.

        The function will execute the benchmark
        and return the result
        """
        scenarios = {}

        for recommender in self.scenario_config.recommender:
            campaign = Campaign(
                searchspace=SearchSpace.from_product(
                    parameters=self.benchmark_domain.parameters
                ),
                objective=self.benchmark_domain.objective,
                recommender=recommender,
            )
            recommender_name = recommender.__class__.__name__
            if recommender_name in scenarios:
                recommender_name = f"{recommender_name}_{str(uuid4())}"
            scenarios[recommender_name] = campaign

        metadata = {
            "n_doe_iterations": str(self.scenario_config.n_doe_iterations),
            "batch_size": str(self.scenario_config.batch_size),
            "n_mc_iterations": str(self.scenario_config.n_mc_iterations),
            "date": str(datetime.now().isoformat()),
            "benchmark_name": self.benchmark_domain.name,
            "benchmark_description": self.benchmark_domain.description,
            "benchmark_id": str(self.identifier),
        }

        start_ns = time.perf_counter_ns()
        result = simulate_scenarios(
            scenarios,
            self.benchmark_domain.get_lookup(),
            batch_size=self.scenario_config.batch_size,
            n_doe_iterations=self.scenario_config.n_doe_iterations,
            n_mc_iterations=self.scenario_config.n_mc_iterations,
        )
        stop_ns = time.perf_counter_ns()
        time_delta = stop_ns - start_ns
        benchmark_result = Result(self.identifier, metadata, result, time_delta)
        return benchmark_result
