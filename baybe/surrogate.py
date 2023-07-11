# pylint: disable=too-few-public-methods
"""
Surrogate models, such as Gaussian processes, random forests, etc.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, ClassVar, Optional, Tuple, Type

import cattrs

import numpy as np
import torch
from attrs import define, field
from botorch.fit import fit_gpytorch_mll_torch
from botorch.models import SingleTaskGP
from botorch.models.transforms.input import Normalize
from botorch.models.transforms.outcome import Standardize
from gpytorch.kernels.matern_kernel import MaternKernel
from gpytorch.kernels.scale_kernel import ScaleKernel
from gpytorch.likelihoods import GaussianLikelihood
from gpytorch.means import ConstantMean
from gpytorch.mlls import ExactMarginalLogLikelihood
from gpytorch.priors.torch_priors import GammaPrior
from ngboost import NGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ARDRegression
from torch import Tensor

from baybe.scaler import DefaultScaler
from baybe.searchspace import SearchSpace
from baybe.utils import get_base_unstructure_hook, unstructure_base
from baybe.utils.serialization import SerialMixin

# Use float64 (which is recommended at least for BoTorch models)
_DTYPE = torch.float64

# Define constants
_MIN_TARGET_STD = 1e-6
_MIN_VARIANCE = 1e-6


def _prepare_inputs(x: Tensor) -> Tensor:
    """Helper function to validate and prepare the model input."""
    if len(x) == 0:
        raise ValueError("The model input must be non-empty.")
    return x.to(_DTYPE)


def _prepare_targets(y: Tensor) -> Tensor:
    """Helper function to validate and prepare the model targets."""
    if y.shape[1] != 1:
        raise NotImplementedError(
            "The model currently supports only one target or multiple targets in "
            "DESIRABILITY mode."
        )
    return y.to(_DTYPE)


def _var_to_covar(var: Tensor) -> Tensor:
    """
    Converts a tensor (with optional batch dimensions) that contains (marginal)
    variances along its last dimension into one that contains corresponding diagonal
    covariance matrices along its last two dimensions.
    """
    return torch.diag_embed(var)


def _get_model_params_validator(model_init: Callable) -> Callable:
    """Constructs a validator based on the model class"""

    def validate_model_params(obj, _, model_params: dict) -> None:
        # Get model class name
        model = obj.__class__.__name__

        # GP does not support additional model params
        if "GaussianProcess" in model and model_params:
            raise ValueError(f"{model} does not support model params.")

        # Invalid params
        invalid_params = ", ".join(
            [
                key
                for key in model_params.keys()
                if key not in model_init.__code__.co_varnames
            ]
        )

        if invalid_params:
            raise ValueError(f"Invalid model params for {model}: {invalid_params}.")

    return validate_model_params


def catch_constant_targets(model_cls: Type[SurrogateModel]):
    """
    Wraps a given `SurrogateModel` class that cannot handle constant training target
    values such that these cases are handled by a separate model type.
    """

    class SplitModel(SurrogateModel):
        """
        A surrogate model that applies a separate strategy for cases where the training
        targets are all constant and no variance can be estimated.
        """

        # The posterior mode is chosen to match that of the wrapped model class
        joint_posterior: ClassVar[bool] = model_cls.joint_posterior

        def __init__(self, *args, **kwargs):
            """Stores an instance of the underlying model class."""
            super().__init__()
            self.model = model_cls(*args, **kwargs)
            self.__class__.__name__ = self.model.__class__.__name__
            self.model_params = self.model.model_params

        def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
            """Calls the posterior function of the internal model instance."""
            mean, var = self.model._posterior(  # pylint: disable=protected-access
                candidates
            )

            # If a joint posterior is expected but the model has been overriden by one
            # that does not provide covariance information, construct a diagonal
            # covariance matrix
            if self.joint_posterior and not self.model.joint_posterior:
                var = _var_to_covar(var)

            return mean, var

        def _fit(
            self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor
        ) -> None:
            """Selects a model based on the variance of the targets and fits it."""

            # https://github.com/pytorch/pytorch/issues/29372
            # Needs 'unbiased=False' (otherwise, the result will be NaN for scalars)
            if torch.std(train_y.ravel(), unbiased=False) < _MIN_TARGET_STD:
                self.model = MeanPredictionModel()

            # Fit the selected model with the training data
            self.model.fit(searchspace, train_x, train_y)

        def __getattribute__(self, attr):
            """
            Accesses the attributes of the class instance if available, otherwise uses
            the attributes of the internal model instance.
            """
            # Try to retrieve the attribute in the class
            try:
                val = super().__getattribute__(attr)
            except AttributeError:
                pass
            else:
                return val

            # If the attribute has not been overwritten, use that of the internal model
            return self.model.__getattribute__(attr)

    return SplitModel


def scale_model(model_cls: Type[SurrogateModel]):
    """
    Wraps a given `SurrogateModel` class such that it operates with scaled
    representations of the training and test data.
    """

    class ScaledModel(model_cls):
        """Overrides the methods of the given model class such the use scaled data."""

        def __init__(self, *args, **kwargs):
            """Stores an instance of the underlying model class and a scaler object."""
            self.model = model_cls(*args, **kwargs)
            self.__class__.__name__ = self.model.__class__.__name__
            self.model_params = self.model.model_params
            self.scaler = None

        def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
            """
            Calls the posterior function of the internal model instance on
            a scaled version of the test data and rescales the output accordingly.
            """
            candidates = self.scaler.transform(candidates)
            mean, covar = self.model._posterior(  # pylint: disable=protected-access
                candidates
            )
            return self.scaler.untransform(mean, covar)

        def _fit(
            self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor
        ) -> None:
            """Fits the scaler and the model using the scaled training data."""
            self.scaler = DefaultScaler(searchspace.discrete.comp_rep)
            train_x, train_y = self.scaler.fit_transform(train_x, train_y)
            self.model.fit(searchspace, train_x, train_y)

        def __getattribute__(self, attr):
            """
            Accesses the attributes of the class instance if available, otherwise uses
            the attributes of the internal model instance.
            """
            # Try to retrieve the attribute in the class
            try:
                val = super().__getattribute__(attr)
            except AttributeError:
                pass
            else:
                return val

            # If the attribute has not been overwritten, use that of the internal model
            return self.model.__getattribute__(attr)

    return ScaledModel


def batchify(
    posterior: Callable[[SurrogateModel, Tensor], Tuple[Tensor, Tensor]]
) -> Callable[[SurrogateModel, Tensor], Tuple[Tensor, Tensor]]:
    """
    Wraps `SurrogateModel` posterior functions that are incompatible with t- and
    q-batching such that they become able to process batched inputs.
    """

    @wraps(posterior)
    def sequential_posterior(
        model: SurrogateModel, candidates: Tensor
    ) -> [Tensor, Tensor]:
        """A posterior function replacement that processes batches sequentially."""

        # If no batch dimensions are given, call the model directly
        if candidates.ndim == 2:
            return posterior(model, candidates)

        # Keep track of batch dimensions
        t_shape = candidates.shape[:-2]
        q_shape = candidates.shape[-2]

        # If the posterior function provides full covariance information, call it
        # t-batch by t-batch
        if model.joint_posterior:  # pylint: disable=no-else-return

            # Flatten all t-batch dimensions into a single one
            flattened = candidates.flatten(end_dim=-3)

            # Call the model on each (flattened) t-batch
            out = (posterior(model, batch) for batch in flattened)

            # Collect the results and restore the batch dimensions
            mean, covar = zip(*out)
            mean = torch.reshape(torch.stack(mean), t_shape + (q_shape,))
            covar = torch.reshape(torch.stack(covar), t_shape + (q_shape, q_shape))

            return mean, covar

        # Otherwise, flatten all t- and q-batches into a single q-batch dimension
        # and evaluate the posterior function in one go
        else:

            # Flatten *all* batches into the q-batch dimension
            flattened = candidates.flatten(end_dim=-2)

            # Call the model on the entire input
            mean, var = posterior(model, flattened)

            # Restore the batch dimensions
            mean = torch.reshape(mean, t_shape + (q_shape,))
            var = torch.reshape(var, t_shape + (q_shape,))

            return mean, var

    return sequential_posterior


@define
class SurrogateModel(ABC, SerialMixin):
    """Abstract base class for all surrogate models."""

    joint_posterior: ClassVar[bool]
    model_params: dict = field(default={})

    def posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
        """
        Evaluates the surrogate model at the given candidate points.

        Parameters
        ----------
        candidates : torch.Tensor
            The candidate points, represented as a tensor of shape (*t, q, d), where
            't' denotes the "t-batch" shape, 'q' denotes the "q-batch" shape, and
            'd' is the input dimension. For more details about batch shapes, see:
            https://botorch.org/docs/batching

        Returns
        -------
        Tuple[Tensor, Tensor]
            The posterior means and posterior covariance matrices of the t-batched
            candidate points.
        """
        # Prepare the input
        candidates = _prepare_inputs(candidates)

        # Evaluate the posterior distribution
        mean, covar = self._posterior(candidates)

        # Apply covariance transformation for marginal posterior models
        if not self.joint_posterior:
            covar = _var_to_covar(covar)

        # Add small diagonal variances for numerical stability
        covar.add_(torch.eye(covar.shape[-1]) * _MIN_VARIANCE)

        return mean, covar

    @abstractmethod
    def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
        """
        Implements the actual posterior evaluation logic. In contrast to its public
        counterpart, no data validation/transformation is carried out but only the raw
        posterior computation is conducted.

        Note:
        -----
        The public `posterior` method *always* returns a full covariance matrix. By
        contrast, this method may return either a covariance matrix or a tensor
        of marginal variances, depending on the models `joint_posterior` flag. The
        optional conversion to a covariance matrix is handled by the public method.
        """

    def fit(self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor) -> None:
        """Trains the surrogate model on the provided data."""
        # TODO: Adjust scale_model decorator to support other model types as well.
        if (not searchspace.continuous.is_empty) and (self.type != "GP"):
            raise NotImplementedError(
                "Continuous search spaces are currently only supported by GPs."
            )

        # Validate and prepare the training data
        train_x = _prepare_inputs(train_x)
        train_y = _prepare_targets(train_y)

        return self._fit(searchspace, train_x, train_y)

    @abstractmethod
    def _fit(self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor) -> None:
        """
        Implements the actual fitting logic. In contrast to its public counterpart,
        no data validation/transformation is carried out but only the raw fitting
        operation is conducted.
        """


@define
class GaussianProcessModel(SurrogateModel):
    """A Gaussian process surrogate model."""

    joint_posterior: ClassVar[bool] = True
    model: Optional[SingleTaskGP] = field(init=False, default=None)
    model_params: dict = field(
        default={},
        converter=dict,
        validator=_get_model_params_validator(SingleTaskGP.__init__),
    )

    def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
        """See base class."""
        posterior = self.model.posterior(candidates)
        return posterior.mvn.mean, posterior.mvn.covariance_matrix

    def _fit(self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor) -> None:
        """See base class."""

        # Get the input bounds from the search space in BoTorch Format
        bounds = searchspace.param_bounds_comp
        # TODO: use target value bounds when explicitly provided

        # define the input and outcome transforms
        # TODO [Scaling]: scaling should be handled by searchspace object
        input_transform = Normalize(train_x.shape[1], bounds=bounds)
        outcome_transform = Standardize(train_y.shape[1])

        # ---------- GP prior selection ---------- #
        # TODO: temporary prior choices adapted from edbo, replace later on

        mordred = searchspace.contains_mordred or searchspace.contains_rdkit
        if mordred and train_x.shape[-1] < 50:
            mordred = False

        # low D priors
        if train_x.shape[-1] < 5:
            lengthscale_prior = [GammaPrior(1.2, 1.1), 0.2]
            outputscale_prior = [GammaPrior(5.0, 0.5), 8.0]
            noise_prior = [GammaPrior(1.05, 0.5), 0.1]

        # DFT optimized priors
        elif mordred and train_x.shape[-1] < 100:
            lengthscale_prior = [GammaPrior(2.0, 0.2), 5.0]
            outputscale_prior = [GammaPrior(5.0, 0.5), 8.0]
            noise_prior = [GammaPrior(1.5, 0.1), 5.0]

        # Mordred optimized priors
        elif mordred:
            lengthscale_prior = [GammaPrior(2.0, 0.1), 10.0]
            outputscale_prior = [GammaPrior(2.0, 0.1), 10.0]
            noise_prior = [GammaPrior(1.5, 0.1), 5.0]

        # OHE optimized priors
        else:
            lengthscale_prior = [GammaPrior(3.0, 1.0), 2.0]
            outputscale_prior = [GammaPrior(5.0, 0.2), 20.0]
            noise_prior = [GammaPrior(1.5, 0.1), 5.0]

        # ---------- End: GP prior selection ---------- #

        # extract the batch shape of the training data
        batch_shape = train_x.shape[:-2]

        # create GP mean
        mean_module = ConstantMean(batch_shape=batch_shape)

        # create GP covariance
        covar_module = ScaleKernel(
            MaternKernel(
                nu=2.5,
                ard_num_dims=train_x.shape[-1],
                batch_shape=batch_shape,
                lengthscale_prior=lengthscale_prior[0],
            ),
            batch_shape=batch_shape,
            outputscale_prior=outputscale_prior[0],
        )
        covar_module.outputscale = torch.tensor([outputscale_prior[1]])
        covar_module.base_kernel.lengthscale = torch.tensor([lengthscale_prior[1]])

        # create GP likelihood
        likelihood = GaussianLikelihood(
            noise_prior=noise_prior[0], batch_shape=batch_shape
        )
        likelihood.noise = torch.tensor([noise_prior[1]])

        # construct and fit the Gaussian process
        self.model = SingleTaskGP(
            train_x,
            train_y,
            input_transform=input_transform,
            outcome_transform=outcome_transform,
            mean_module=mean_module,
            covar_module=covar_module,
            likelihood=likelihood,
        )
        mll = ExactMarginalLogLikelihood(self.model.likelihood, self.model)
        # IMPROVE: The step_limit=100 stems from the former (deprecated)
        #  `fit_gpytorch_torch` function, for which this was the default. Probably,
        #   one should use a smarter logic here.
        fit_gpytorch_mll_torch(mll, step_limit=100)


@define
class MeanPredictionModel(SurrogateModel):
    """
    A trivial surrogate model that provides the average value of the training targets
    as posterior mean and a (data-independent) constant posterior variance.
    """

    joint_posterior: ClassVar[bool] = False
    target_value = None

    @batchify
    def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
        """See base class."""
        # TODO: use target value bounds for covariance scaling when explicitly provided
        mean = self.target_value * torch.ones([len(candidates)])
        var = torch.ones(len(candidates))
        return mean, var

    def _fit(self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor) -> None:
        """See base class."""
        self.target_value = train_y.mean().item()


@catch_constant_targets
@scale_model
@define
class RandomForestModel(SurrogateModel):
    """A random forest surrogate model."""

    joint_posterior: ClassVar[bool] = False
    model: Optional[RandomForestRegressor] = field(init=False, default=None)
    model_params: dict = field(
        default={},
        converter=dict,
        validator=_get_model_params_validator(RandomForestRegressor.__init__),
    )

    @batchify
    def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
        """See base class."""

        # Evaluate all trees
        # NOTE: explicit conversion to ndarray is needed due to a pytorch issue:
        # https://github.com/pytorch/pytorch/pull/51731
        # https://github.com/pytorch/pytorch/issues/13918
        predictions = torch.from_numpy(
            np.asarray(
                [
                    self.model.estimators_[tree].predict(candidates)
                    for tree in range(self.model.n_estimators)
                ]
            )
        )

        # Compute posterior mean and variance
        mean = predictions.mean(dim=0)
        var = predictions.var(dim=0)

        return mean, var

    def _fit(self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor) -> None:
        """See base class."""
        self.model = RandomForestRegressor(**(self.model_params))
        self.model.fit(train_x, train_y.ravel())


@catch_constant_targets
@scale_model
@define
class NGBoostModel(SurrogateModel):
    """A natural-gradient-boosting surrogate model."""

    joint_posterior: ClassVar[bool] = False
    model: Optional[NGBRegressor] = field(init=False, default=None)
    model_params: dict = field(
        default={"n_estimators": 25, "verbose": False},
        converter=dict,
        validator=_get_model_params_validator(NGBRegressor.__init__),
    )

    @batchify
    def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
        """See base class."""
        # Get predictions
        dists = self.model.pred_dist(candidates)

        # Split into posterior mean and variance
        mean = torch.from_numpy(dists.mean())
        var = torch.from_numpy(dists.var)

        return mean, var

    def _fit(self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor) -> None:
        """See base class."""
        self.model = NGBRegressor(**(self.model_params)).fit(train_x, train_y.ravel())


@catch_constant_targets
@scale_model
@define
class BayesianLinearModel(SurrogateModel):
    """A Bayesian linear regression surrogate model."""

    joint_posterior: ClassVar[bool] = False
    model: Optional[ARDRegression] = field(init=False, default=None)
    model_params: dict = field(
        default={},
        converter=dict,
        validator=_get_model_params_validator(ARDRegression.__init__),
    )

    @batchify
    def _posterior(self, candidates: Tensor) -> Tuple[Tensor, Tensor]:
        """See base class."""
        # Get predictions
        dists = self.model.predict(candidates.numpy(), return_std=True)

        # Split into posterior mean and variance
        mean = torch.from_numpy(dists[0])
        var = torch.from_numpy(dists[1]).pow(2)

        return mean, var

    def _fit(self, searchspace: SearchSpace, train_x: Tensor, train_y: Tensor) -> None:
        """See base class."""
        self.model = ARDRegression(**(self.model_params))
        self.model.fit(train_x, train_y.ravel())


def remove_model(raw_unstructure_hook):
    """Removes the model in an surrogate for serialization"""

    def wrapper(obj):
        dict_ = raw_unstructure_hook(obj)
        try:
            dict_.pop("model")
        except KeyError:
            pass
        return dict_

    return wrapper


# Register (un-)structure hooks
cattrs.register_unstructure_hook(SurrogateModel, remove_model(unstructure_base))
cattrs.register_structure_hook(
    SurrogateModel, get_base_unstructure_hook(SurrogateModel)
)
