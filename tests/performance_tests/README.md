# Description

This folder contains performance tests which reflect long running experimental scenarios. They are not meant to be run manually since their execution time is typically long. However, if you want to run them, you can do so by executing the following tox command:

```bash
tox -e performancetest-py310
```

These tests should reflect the performance of the codebase and should be used to identify performance regressions which may only visible in long running scenarios. We refer to performance in a quality oriented way, meaning that we are especially interested in the convergence behavior of the provided algorithms and strategies. The performance tests are not meant to be used for classical compute benchmarking purposes, but rather to ensure that the codebase is able to solve the given optimization problems in a consistent and reliable way. To compare the performance of different versions of the codebase properly, we store the results of the performance tests either as csv files if run locally or in a database if run on a CI system. All tests run as normal pytest parametrized tests and are executed in parallel by the pytest-xdist plugin.

## Adding a new test case

Each scenario type of BayBE is represented by a separate test case. These are collected in the `test_cases` folder where a file for each test scenario type a list of the respective test case class is provided. Here, a new entry can be added which holds the parameter for executing the simulation. For adding or reusing parameter and lookups, the folder `test_cases/data` holds dictoraries for the respective parameter in the `parameter.py` file and the lookup tables in the `lookups.py` file. The Keyes are used to reference the parameter and lookups in the test scenarios, making them more readable and maintainable. Lookups are often saved as csv files which is done under the `test_cases/data/lookup_data` folder. For including a callable for the lookup or parameter, files are provided to implement the respective function under `test_cases/data/gen_lookup_functions.py` for Lookups and `test_cases/data/gen_parameter_functions.py` for parameters. Datasets can also be build there if needed.

### Example for adding the experiment test case cell_media

1. Add the lookup csv file `cell_media.csv` to the `test_cases/data/lookup_data` folder
2. Reference the lookup in the `test_cases/data/lookups.py` file by adding the following line:

    ```python
    [...]
    "cell_media": read_csv(PATH_PREFIX.joinpath("cell_media.csv").resolve()),
    [...]
    ```

    The key string "cell_media" is used to reference the lookup in the `simulate_experiment_test.py` file.
3. Add the parameter to the `test_cases/data/parameter.py` file by adding the following line:

    ```python
    [...]
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
    [...]
    ```

    Where the key string "cell_media" again is used to reference the parameter in the `simulate_experiment_test.py` file.
4. Add a new test case object of the type `SimulateExperimentTestCase` the the `simulate_experiment_test.py` file:

    ```python
    [...]
    SimulateExperimentTestCase(
        unique_id=UUID("144b6de4-b6c1-4a23-9eac-6e290188e5c5"),
        title="Cell Media Simulation maximum titer",
        campaign=Campaign(
            searchspace=SearchSpace.from_product(
                parameters=PARAMETER_COMBINATION["cell_media"]
            ),
            objective=SingleTargetObjective(
                target=NumericalTarget(name="titer", mode=TargetMode.MAX)
            ),
        ),
        lookup=LOOKUP_STRUCTURE["cell_media"],
        batch_size=2,
        n_doe_iterations=10,
    ),
    [...]
    ```

    It is important that every test case has a unique UUID which is used to identify the test case over time. A UUID is used to avoid self speaking titles for identification since they may have to change over time because the meaning doesn't express the content any longer after some code changes. The UUID must be unique and generated by you. You may want to use an online the UUID generator like [https://www.uuidgenerator.net/](https://www.uuidgenerator.net/). So the title provided only supports the readability of the test case and is not used for identification. As you can see, the parameters are referenced by the key string "cell_media" for the imported dictionary `PARAMETER_COMBINATION` and `LOOKUP_STRUCTURE`. All other settings follow the information necessary for executing the simulation. Please refer to the BayBE documentation for further information on the meaning of the parameters for each simulation type under the [simulation submodule](./../../docs/userguide/simulation.md).

## Persisting test results

For persisting the test result in the CI/CD, currently a S3-Bucket name is used. This name must be set in the environment variable `BAYBE_PERFORMANCE_PERSISTANCE_PATH` in the CI/CD system. The test results are stored under the key `UUID/BRANCH_NAME/BAYBE_VERSION/DATE_TIME_ISO/COMMIT_HASH` as a csv file. The created S3 entry contains information like the batch size and the number of DOE iterations, but also the execution time and the title of the test case. If the environment variable is not set, the test results are stored locally in the `tests/performance_tests/results` folder. The test results are stored as csv files with the name `UUID-BAYBE_VERSION-DATE_TIME_ISO.csv` without additional metadata.

### How test results are loaded

Differences in loading a result for comparison is only available within the CI/CD environment. For local usage, the oldest result is loaded if available. There are two loading scenarios depending on where the performance test is started:

- From the main branch: The latest result from the previous release of BayBE is loaded to compare the current stable version with the previous stable version.

- From a feature branch: The latest result from the current main branch is loaded to compare the current feature branch with the main branch.

### How test results are compared

This has to be implemented and is not yet available.
