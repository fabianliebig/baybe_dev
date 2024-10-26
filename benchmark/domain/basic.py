"""Encapsulate the domain logic of the application."""

import ast
import base64
import io
import json
from collections.abc import Callable
from typing import Any

import pandas as pd
from attrs import define, field
from attrs.validators import instance_of
from pandas import DataFrame

from baybe.constraints.base import Constraint
from baybe.objectives.base import Objective, to_objective
from baybe.parameters.base import Parameter
from benchmark.domain.math_function_eval_utils import MathFunctionEvalUtils


@define(frozen=True)
class Domain:
    """The domain which the benchmark is build upon."""

    name: str = field(validator=instance_of(str))
    """The name of the domain."""

    description: str = field(validator=instance_of(str))
    """The description of the domain."""

    parameters: list[Parameter] = field()
    """The parameters of the domain. Those will be seperated into
    the different parameter groups. See :module:`baybe.parameters.base`."""

    objective: Objective = field(
        validator=instance_of(Objective), converter=to_objective
    )
    """The objective of the domain. See :module:`baybe.objective.base`."""

    lookup: str | DataFrame = field(validator=instance_of((str, DataFrame)))
    """The lookup table of the domain. If a string is provided it will be
    interpreted as a mathematical function which is used as a callback."""

    constraints: list[Constraint] = field(default=[])
    """The constraints of the domain. See :module:`baybe.constraints.base`."""

    _type_separated_parameters: dict[type, list[Parameter]] = field(
        init=False, default={}
    )
    """The type separated parameters of the domain based on the
    actual class type."""

    @parameters.validator
    def _validate_parameters(self, _: Any, parameters: list[Parameter]) -> None:
        """Validate the parameters of the domain.

        The function will validate the parameters of the domain and raise an
        error if the parameters are not valid.
        """
        assert isinstance(parameters, list)
        for parameter in parameters:
            assert isinstance(parameter, Parameter)

    @lookup.validator
    def _validate_lookup(self, _: Any, lookup: str | DataFrame) -> None:
        """Validate the lookup table of the domain.

        The function will validate the lookup table of the domain and raise an
        error if the lookup table is not valid.
        """
        if not isinstance(lookup, (str, DataFrame)):
            raise ValueError("Invalid lookup type.")

        if isinstance(lookup, str):
            MathFunctionEvalUtils._is_string_math_evaluation_safety(lookup)

    @constraints.validator
    def _validate_constraints(self, _: Any, constraints: list[Constraint]) -> None:
        """Validate the constraints of the domain.

        The function will validate the constraints of the domain and raise an
        error if the constraints are not valid.
        """
        assert isinstance(constraints, list)
        for constraint in constraints:
            assert isinstance(constraint, Constraint)

    def __attrs_post_init__(self):
        """Post initialize the domain."""
        for parameter in self.parameters:
            if type(parameter) not in self._type_separated_parameters:
                self._type_separated_parameters[type(parameter)] = []
            self._type_separated_parameters[type(parameter)].append(parameter)

    def get_parameter_list_by_type(self, parameter_type: type) -> list[Parameter]:
        """Get the parameter list by the parameter type.

        Args:
            parameter_type: The type of the parameter.

        Returns:
            The list of parameters by the parameter type.
        """
        return self._type_separated_parameters.get(parameter_type, [])

    def _match_parameter_names_with_values(
        self, args: tuple[int | float]
    ) -> dict[str, float | int]:
        """Match the parameter names with the values."""
        assert len(args) == len(self.parameters)
        restructured_args_since_order_is_backwards = args[::-1]
        return {
            parameter.name: value
            for parameter, value in zip(
                self.parameters, restructured_args_since_order_is_backwards
            )
        }

    def _callable_parsing_lookup(self, *args) -> float:
        """Parse the lookup table as a callable."""
        if not all(isinstance(value, (int, float)) for value in args):
            raise ValueError("Invalid input arg type.")
        if not self.lookup or not isinstance(self.lookup, str):
            raise ValueError("Invalid lookup type.")
        variable_input_dict = self._match_parameter_names_with_values(args)
        variable_replaced_lookup = self.lookup
        for variable, value in variable_input_dict.items():
            if not isinstance(value, (int, float)):
                raise ValueError("Invalid input arg type.")
            variable_replaced_lookup = variable_replaced_lookup.replace(
                variable, str(value)
            )
        calculation_tree = ast.parse(variable_replaced_lookup, mode="eval")
        return MathFunctionEvalUtils.more_safe_eval(calculation_tree.body)

    def get_lookup(self) -> Callable | DataFrame:
        """Get the lookup table as a callable or dataframe.

        Returns:
            The lookup table as a callable or a dataframe.

        Raises:
            ValueError: If the lookup type is not supported.
        """
        if isinstance(self.lookup, DataFrame):
            return self.lookup
        if isinstance(self.lookup, str):
            return self._callable_parsing_lookup
        raise ValueError("Invalid lookup type.")

    def _get_document_list_from_parameters(self) -> list[dict]:
        """Create a list of documents (dicts) from the parameters.

        Returns:
            The parameters as a list of documents.
        """
        document_parameter_list = []
        for parameter in self.parameters:
            document_parameter_list.append(parameter.to_dict())
        return document_parameter_list

    def _get_constraint_document_list(self) -> list[dict]:
        """Create a list of documents (dicts) from the constraints."""
        document_constraint_list = []
        for constraint in self.constraints:
            document_constraint_list.append(constraint.to_dict())
        return document_constraint_list

    def _get_serialized_lookup(self) -> dict:
        """Serialize the lookup table.

        The function will serialize the lookup table to a string.

        Returns:
            The serialized lookup table as a string.

        Raises:
            ValueError: If the lookup type is not supported.
        """
        if isinstance(self.lookup, DataFrame):
            csv_string = self.lookup.to_csv(index=False)
            base64_bytes = base64.b64encode(csv_string.encode("utf-8"))
            return {"type": "DataFrame", "data": base64_bytes.decode("utf-8")}
        if isinstance(self.lookup, str):
            return {"type": "str", "data": self.lookup}
        raise ValueError("Invalid lookup type.")

    def to_dict(self) -> dict:
        """Return the domain as a dictionary.

        Returns:
            The domain as a dictionary with the lookup as .
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_document_list_from_parameters(),
            "objective": self.objective.to_dict(),
            "constraints": self._get_constraint_document_list(),
            "lookup": self._get_serialized_lookup(),
        }

    def to_json(self) -> str:
        """Return the domain as a JSON string.

        Returns:
            The domain as a JSON string.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, domain_dict: dict) -> "Domain":
        """Create a domain from a dictionary.

        Args:
            domain_dict: The dictionary to create the domain from.

        Returns:
            The domain created from the dictionary.
        """
        deserializes_lookup = cls._deserialize_lookup(domain_dict)
        return cls(
            name=domain_dict["name"],
            description=domain_dict["description"],
            parameters=[
                Parameter.from_dict(parameter_dict)
                for parameter_dict in domain_dict["parameters"]
            ],
            objective=Objective.from_dict(domain_dict["objective"]),
            lookup=deserializes_lookup,
            constraints=[
                Constraint.from_dict(constraint_dict)
                for constraint_dict in domain_dict["constraints"]
            ],
        )

    @classmethod
    def _deserialize_lookup(cls, domain_dict: dict) -> DataFrame | str:
        """Deserialize a lookup from a dictionary.

        This method takes a dictionary representation of a lookup and deserializes it
        into either a pandas DataFrame or a string, depending on the type specified in
        the dictionary.

        Args:
            domain_dict: A dictionary containing the lookup information.
                It must have a "lookup" key with a nested dictionary that includes
                "type" and "data" keys.

        Returns:
            The deserialized lookup, which can be either a
                pandas DataFrame if the type is "DataFrame"
                or a string if the type is "str".

        Raises:
            ValueError: If the lookup type is not "DataFrame"
                or "str", or if the data for type "str" is not a string.
        """
        deserializes_lookup = domain_dict["lookup"]
        if deserializes_lookup["type"] == "DataFrame":
            csv_string = base64.b64decode(deserializes_lookup["data"]).decode("utf-8")
            return pd.read_csv(io.StringIO(csv_string))

        TYPE_IS_STR = deserializes_lookup["type"] == "str" and isinstance(
            deserializes_lookup["data"], str
        )
        if TYPE_IS_STR:
            return deserializes_lookup["data"]
        raise ValueError("Invalid lookup type.")

    @classmethod
    def from_json(cls, domain_json: str) -> "Domain":
        """Create a domain from a JSON string.

        Args:
            domain_json: The JSON string to create the domain from.

        Returns:
            The domain created from the JSON string.
        """
        return cls.from_dict(json.loads(domain_json))
