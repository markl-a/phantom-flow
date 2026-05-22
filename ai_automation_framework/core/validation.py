"""
Comprehensive data validation framework for AI Automation Framework.

This module provides a flexible and powerful validation system with built-in validators,
composite validators, schema validation, and async support.
"""

import re
import inspect
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
)
from functools import wraps
from urllib.parse import urlparse
import asyncio

try:
    from pydantic import BaseModel, ValidationError as PydanticValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    PydanticValidationError = Exception


class ValidationError(Exception):
    """Base exception for validation errors."""

    def __init__(self, message: str, field_path: Optional[str] = None, errors: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field_path: Dot-separated path to the field that failed validation
            errors: List of detailed error dictionaries
        """
        self.message = message
        self.field_path = field_path
        self.errors = errors or []
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with field path."""
        if self.field_path:
            return f"Validation failed for '{self.field_path}': {self.message}"
        return f"Validation failed: {self.message}"

    def add_error(self, field: str, message: str) -> None:
        """
        Add an error to the error list.

        Args:
            field: Field name or path
            message: Error message
        """
        self.errors.append({"field": field, "message": message})

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "message": self.message,
            "field_path": self.field_path,
            "errors": self.errors,
        }


class ValidatorBase(ABC):
    """
    Base class for all validators.

    Validators can be chained together for complex validation rules.
    """

    def __init__(self, error_message: Optional[str] = None):
        """
        Initialize validator.

        Args:
            error_message: Custom error message
        """
        self.error_message = error_message
        self._next_validator: Optional['ValidatorBase'] = None

    @abstractmethod
    def validate(self, value: Any, field_path: str = "") -> Any:
        """
        Validate a value.

        Args:
            value: Value to validate
            field_path: Dot-separated path to the field being validated

        Returns:
            The validated value (possibly transformed)

        Raises:
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """
        Asynchronously validate a value.

        Args:
            value: Value to validate
            field_path: Dot-separated path to the field being validated

        Returns:
            The validated value (possibly transformed)

        Raises:
            ValidationError: If validation fails
        """
        pass

    def chain(self, validator: 'ValidatorBase') -> 'ValidatorBase':
        """
        Chain another validator after this one.

        Args:
            validator: Validator to chain

        Returns:
            The chained validator for method chaining
        """
        self._next_validator = validator
        return validator

    def _run_next(self, value: Any, field_path: str = "") -> Any:
        """Run the next validator in the chain if present."""
        if self._next_validator:
            return self._next_validator.validate(value, field_path)
        return value

    async def _run_next_async(self, value: Any, field_path: str = "") -> Any:
        """Run the next validator in the chain asynchronously if present."""
        if self._next_validator:
            return await self._next_validator.validate_async(value, field_path)
        return value

    def __call__(self, value: Any, field_path: str = "") -> Any:
        """Allow validator to be called directly."""
        return self.validate(value, field_path)


class Required(ValidatorBase):
    """Validator to ensure a value is not None or empty."""

    def __init__(self, allow_empty: bool = False, error_message: Optional[str] = None):
        """
        Initialize Required validator.

        Args:
            allow_empty: If True, allow empty strings/lists/dicts but not None
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.allow_empty = allow_empty

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that value is not None or empty."""
        if value is None:
            raise ValidationError(
                self.error_message or "Value is required",
                field_path
            )

        if not self.allow_empty:
            if isinstance(value, (str, list, dict, set, tuple)) and len(value) == 0:
                raise ValidationError(
                    self.error_message or "Value cannot be empty",
                    field_path
                )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


class TypeValidator(ValidatorBase):
    """Validator to check if value matches expected type(s)."""

    def __init__(self, expected_type: Union[Type, Tuple[Type, ...]], error_message: Optional[str] = None):
        """
        Initialize Type validator.

        Args:
            expected_type: Expected type or tuple of types
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.expected_type = expected_type

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that value matches expected type."""
        if not isinstance(value, self.expected_type):
            type_names = (
                self.expected_type.__name__
                if isinstance(self.expected_type, type)
                else ", ".join(t.__name__ for t in self.expected_type)
            )
            raise ValidationError(
                self.error_message or f"Expected type {type_names}, got {type(value).__name__}",
                field_path
            )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


class Range(ValidatorBase):
    """Validator to check if numeric value is within a range."""

    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        inclusive: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Initialize Range validator.

        Args:
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            inclusive: If True, min/max values are included in range
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.min_value = min_value
        self.max_value = max_value
        self.inclusive = inclusive

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that value is within range."""
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"Range validator requires numeric value, got {type(value).__name__}",
                field_path
            )

        if self.min_value is not None:
            if self.inclusive and value < self.min_value:
                raise ValidationError(
                    self.error_message or f"Value must be >= {self.min_value}",
                    field_path
                )
            elif not self.inclusive and value <= self.min_value:
                raise ValidationError(
                    self.error_message or f"Value must be > {self.min_value}",
                    field_path
                )

        if self.max_value is not None:
            if self.inclusive and value > self.max_value:
                raise ValidationError(
                    self.error_message or f"Value must be <= {self.max_value}",
                    field_path
                )
            elif not self.inclusive and value >= self.max_value:
                raise ValidationError(
                    self.error_message or f"Value must be < {self.max_value}",
                    field_path
                )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


class Length(ValidatorBase):
    """Validator to check the length of strings, lists, dicts, etc."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        exact_length: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize Length validator.

        Args:
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            exact_length: Exact required length
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.min_length = min_length
        self.max_length = max_length
        self.exact_length = exact_length

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate the length of value."""
        try:
            length = len(value)
        except TypeError:
            raise ValidationError(
                f"Length validator requires object with length, got {type(value).__name__}",
                field_path
            )

        if self.exact_length is not None:
            if length != self.exact_length:
                raise ValidationError(
                    self.error_message or f"Length must be exactly {self.exact_length}, got {length}",
                    field_path
                )
        else:
            if self.min_length is not None and length < self.min_length:
                raise ValidationError(
                    self.error_message or f"Length must be at least {self.min_length}, got {length}",
                    field_path
                )

            if self.max_length is not None and length > self.max_length:
                raise ValidationError(
                    self.error_message or f"Length must be at most {self.max_length}, got {length}",
                    field_path
                )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


class Pattern(ValidatorBase):
    """Validator to match value against a regex pattern."""

    def __init__(self, pattern: Union[str, re.Pattern], flags: int = 0, error_message: Optional[str] = None):
        """
        Initialize Pattern validator.

        Args:
            pattern: Regex pattern (string or compiled pattern)
            flags: Regex flags (e.g., re.IGNORECASE)
            error_message: Custom error message
        """
        super().__init__(error_message)
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern, flags)
        else:
            self.pattern = pattern

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that value matches pattern."""
        if not isinstance(value, str):
            raise ValidationError(
                f"Pattern validator requires string value, got {type(value).__name__}",
                field_path
            )

        if not self.pattern.match(value):
            raise ValidationError(
                self.error_message or f"Value does not match pattern {self.pattern.pattern}",
                field_path
            )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


class Email(ValidatorBase):
    """Validator to check if value is a valid email address."""

    # Simple email regex - can be made more complex if needed
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def __init__(self, error_message: Optional[str] = None):
        """
        Initialize Email validator.

        Args:
            error_message: Custom error message
        """
        super().__init__(error_message)

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that value is a valid email."""
        if not isinstance(value, str):
            raise ValidationError(
                f"Email validator requires string value, got {type(value).__name__}",
                field_path
            )

        if not self.EMAIL_PATTERN.match(value):
            raise ValidationError(
                self.error_message or f"Invalid email address: {value}",
                field_path
            )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


class URL(ValidatorBase):
    """Validator to check if value is a valid URL."""

    def __init__(
        self,
        require_scheme: bool = True,
        allowed_schemes: Optional[Set[str]] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize URL validator.

        Args:
            require_scheme: If True, URL must have a scheme (http, https, etc.)
            allowed_schemes: Set of allowed schemes (e.g., {'http', 'https'})
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.require_scheme = require_scheme
        self.allowed_schemes = allowed_schemes or {'http', 'https', 'ftp', 'ftps'}

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that value is a valid URL."""
        if not isinstance(value, str):
            raise ValidationError(
                f"URL validator requires string value, got {type(value).__name__}",
                field_path
            )

        try:
            parsed = urlparse(value)
        except Exception as e:
            raise ValidationError(
                self.error_message or f"Invalid URL: {str(e)}",
                field_path
            )

        if self.require_scheme and not parsed.scheme:
            raise ValidationError(
                self.error_message or "URL must have a scheme (e.g., http://)",
                field_path
            )

        if parsed.scheme and parsed.scheme not in self.allowed_schemes:
            raise ValidationError(
                self.error_message or f"URL scheme must be one of {self.allowed_schemes}",
                field_path
            )

        if not parsed.netloc:
            raise ValidationError(
                self.error_message or "URL must have a network location (domain)",
                field_path
            )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


class Custom(ValidatorBase):
    """Validator that uses a custom validation function."""

    def __init__(
        self,
        validator_func: Callable[[Any], bool],
        error_message: Optional[str] = None,
        async_validator_func: Optional[Callable[[Any], Any]] = None
    ):
        """
        Initialize Custom validator.

        Args:
            validator_func: Function that takes a value and returns True if valid
            error_message: Custom error message
            async_validator_func: Async version of validator function
        """
        super().__init__(error_message)
        self.validator_func = validator_func
        self.async_validator_func = async_validator_func

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate using custom function."""
        try:
            result = self.validator_func(value)
            if not result:
                raise ValidationError(
                    self.error_message or "Custom validation failed",
                    field_path
                )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                self.error_message or f"Custom validation error: {str(e)}",
                field_path
            )

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        try:
            if self.async_validator_func:
                if asyncio.iscoroutinefunction(self.async_validator_func):
                    result = await self.async_validator_func(value)
                else:
                    result = self.async_validator_func(value)
            else:
                result = self.validator_func(value)

            if not result:
                raise ValidationError(
                    self.error_message or "Custom validation failed",
                    field_path
                )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                self.error_message or f"Custom validation error: {str(e)}",
                field_path
            )

        if self._next_validator:
            return await self._run_next_async(value, field_path)
        return value


class And(ValidatorBase):
    """Composite validator that requires all validators to pass."""

    def __init__(self, *validators: ValidatorBase, error_message: Optional[str] = None):
        """
        Initialize And validator.

        Args:
            *validators: Validators that all must pass
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.validators = validators

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that all validators pass."""
        for validator in self.validators:
            value = validator.validate(value, field_path)

        return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        for validator in self.validators:
            value = await validator.validate_async(value, field_path)

        if self._next_validator:
            return await self._run_next_async(value, field_path)
        return value


class Or(ValidatorBase):
    """Composite validator that requires at least one validator to pass."""

    def __init__(self, *validators: ValidatorBase, error_message: Optional[str] = None):
        """
        Initialize Or validator.

        Args:
            *validators: Validators where at least one must pass
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.validators = validators

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that at least one validator passes."""
        errors = []

        for validator in self.validators:
            try:
                value = validator.validate(value, field_path)
                return self._run_next(value, field_path)
            except ValidationError as e:
                errors.append(str(e))

        raise ValidationError(
            self.error_message or f"All validators failed: {'; '.join(errors)}",
            field_path
        )

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        errors = []

        for validator in self.validators:
            try:
                value = await validator.validate_async(value, field_path)
                if self._next_validator:
                    return await self._run_next_async(value, field_path)
                return value
            except ValidationError as e:
                errors.append(str(e))

        raise ValidationError(
            self.error_message or f"All validators failed: {'; '.join(errors)}",
            field_path
        )


class Not(ValidatorBase):
    """Composite validator that inverts another validator's result."""

    def __init__(self, validator: ValidatorBase, error_message: Optional[str] = None):
        """
        Initialize Not validator.

        Args:
            validator: Validator whose result to invert
            error_message: Custom error message
        """
        super().__init__(error_message)
        self.validator = validator

    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate that the wrapped validator fails."""
        try:
            self.validator.validate(value, field_path)
            # If validation passed, we want to fail
            raise ValidationError(
                self.error_message or "Value should not pass validation",
                field_path
            )
        except ValidationError:
            # If validation failed, we want to pass
            return self._run_next(value, field_path)

    async def validate_async(self, value: Any, field_path: str = "") -> Any:
        """Async version of validate."""
        try:
            await self.validator.validate_async(value, field_path)
            # If validation passed, we want to fail
            raise ValidationError(
                self.error_message or "Value should not pass validation",
                field_path
            )
        except ValidationError:
            # If validation failed, we want to pass
            if self._next_validator:
                return await self._run_next_async(value, field_path)
            return value


class Schema:
    """
    Schema validator for dictionaries with multiple fields.

    Allows defining validation rules for each field in a dictionary.
    """

    def __init__(self, schema: Dict[str, Union[ValidatorBase, Type]], strict: bool = False):
        """
        Initialize Schema validator.

        Args:
            schema: Dictionary mapping field names to validators or types
            strict: If True, reject unknown fields
        """
        self.schema = schema
        self.strict = strict

    def _check_unknown_fields(
        self,
        value: Dict[str, Any],
        field_path: str,
        errors: List[Dict[str, Any]]
    ) -> None:
        """
        Check for unknown fields in strict mode.

        Args:
            value: Dictionary being validated
            field_path: Base path for error messages
            errors: List to append errors to
        """
        if self.strict:
            unknown_fields = set(value.keys()) - set(self.schema.keys())
            if unknown_fields:
                errors.append({
                    "field": field_path,
                    "message": f"Unknown fields: {', '.join(unknown_fields)}"
                })

    def _validate_single_field(
        self,
        field_name: str,
        validator: Union[ValidatorBase, Type],
        field_value: Any,
        field_path: str
    ) -> Any:
        """
        Validate a single field.

        Args:
            field_name: Name of the field
            validator: Validator or type to use
            field_value: Value to validate
            field_path: Full path for error messages

        Returns:
            Validated value

        Raises:
            ValidationError: If validation fails
        """
        # Convert type to TypeValidator if needed
        if isinstance(validator, type):
            validator = TypeValidator(validator)

        return validator.validate(field_value, field_path)

    def validate(self, value: Dict[str, Any], field_path: str = "") -> Dict[str, Any]:
        """
        Validate a dictionary against the schema.

        Args:
            value: Dictionary to validate
            field_path: Base path for error messages

        Returns:
            Validated dictionary

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, dict):
            raise ValidationError(
                f"Schema validator requires dict, got {type(value).__name__}",
                field_path
            )

        errors: List[Dict[str, Any]] = []
        result: Dict[str, Any] = {}

        # Check for unknown fields in strict mode
        self._check_unknown_fields(value, field_path, errors)

        # Validate each field
        for field_name, validator in self.schema.items():
            current_path = f"{field_path}.{field_name}" if field_path else field_name
            field_value = value.get(field_name)

            try:
                result[field_name] = self._validate_single_field(
                    field_name, validator, field_value, current_path
                )
            except ValidationError as e:
                errors.append({
                    "field": current_path,
                    "message": e.message
                })

        if errors:
            error_msg = f"Schema validation failed with {len(errors)} error(s)"
            raise ValidationError(error_msg, field_path, errors)

        return result

    async def _validate_field_async(
        self,
        field_name: str,
        validator: Union[ValidatorBase, Type],
        field_value: Any,
        field_path: str
    ) -> Tuple[str, Any, Optional[Dict[str, Any]]]:
        """
        Asynchronously validate a single field.

        Args:
            field_name: Name of the field
            validator: Validator or type to use
            field_value: Value to validate
            field_path: Full path for error messages

        Returns:
            Tuple of (field_name, validated_value, error_dict)
        """
        try:
            # Convert type to TypeValidator if needed
            if isinstance(validator, type):
                validator = TypeValidator(validator)

            validated_value = await validator.validate_async(field_value, field_path)
            return field_name, validated_value, None
        except ValidationError as e:
            return field_name, None, {
                "field": field_path,
                "message": e.message
            }

    async def validate_async(self, value: Dict[str, Any], field_path: str = "") -> Dict[str, Any]:
        """
        Asynchronously validate a dictionary against the schema.

        Args:
            value: Dictionary to validate
            field_path: Base path for error messages

        Returns:
            Validated dictionary

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, dict):
            raise ValidationError(
                f"Schema validator requires dict, got {type(value).__name__}",
                field_path
            )

        errors: List[Dict[str, Any]] = []
        result: Dict[str, Any] = {}

        # Check for unknown fields in strict mode
        self._check_unknown_fields(value, field_path, errors)

        # Validate all fields concurrently
        validation_tasks = [
            self._validate_field_async(
                field_name,
                validator,
                value.get(field_name),
                f"{field_path}.{field_name}" if field_path else field_name
            )
            for field_name, validator in self.schema.items()
        ]

        results = await asyncio.gather(*validation_tasks)

        # Process results
        for field_name, validated_value, error in results:
            if error:
                errors.append(error)
            else:
                result[field_name] = validated_value

        if errors:
            error_msg = f"Schema validation failed with {len(errors)} error(s)"
            raise ValidationError(error_msg, field_path, errors)

        return result


class PydanticValidator(ValidatorBase):
    """Validator that uses Pydantic models for validation."""

    def __init__(self, model: Type[BaseModel], error_message: Optional[str] = None):
        """
        Initialize Pydantic validator.

        Args:
            model: Pydantic model class to validate against
            error_message: Custom error message

        Raises:
            ImportError: If Pydantic is not available
        """
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic is not installed. Install it with: pip install pydantic")

        super().__init__(error_message)
        self.model = model

    def validate(self, value: Any, field_path: str = "") -> BaseModel:
        """Validate using Pydantic model."""
        try:
            if isinstance(value, dict):
                return self.model(**value)
            elif isinstance(value, self.model):
                return value
            else:
                raise ValidationError(
                    f"Expected dict or {self.model.__name__}, got {type(value).__name__}",
                    field_path
                )
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                errors.append({
                    "field": f"{field_path}.{field}" if field_path else field,
                    "message": error['msg']
                })

            raise ValidationError(
                self.error_message or f"Pydantic validation failed",
                field_path,
                errors
            )

    async def validate_async(self, value: Any, field_path: str = "") -> BaseModel:
        """Async version of validate."""
        result = self.validate(value, field_path)
        if self._next_validator:
            return await self._run_next_async(result, field_path)
        return result


def validate_args(**validators: ValidatorBase) -> Callable:
    """
    Decorator to validate function arguments.

    Args:
        **validators: Keyword arguments mapping parameter names to validators

    Returns:
        Decorated function

    Example:
        @validate_args(
            name=Required() & TypeValidator(str) & Length(min_length=1),
            age=Required() & TypeValidator(int) & Range(min_value=0, max_value=150)
        )
        def create_user(name: str, age: int):
            return {"name": name, "age": age}
    """
    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Bind arguments to parameters
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Validate each argument
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    bound.arguments[param_name] = validator.validate(value, param_name)

            return func(**bound.arguments)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Bind arguments to parameters
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Validate each argument
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    bound.arguments[param_name] = await validator.validate_async(value, param_name)

            return await func(**bound.arguments)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


# Convenience function for quick validation
def validate(value: Any, validator: ValidatorBase, field_name: str = "value") -> Any:
    """
    Validate a single value.

    Args:
        value: Value to validate
        validator: Validator to use
        field_name: Name for error messages

    Returns:
        Validated value

    Raises:
        ValidationError: If validation fails
    """
    return validator.validate(value, field_name)


async def validate_async(value: Any, validator: ValidatorBase, field_name: str = "value") -> Any:
    """
    Asynchronously validate a single value.

    Args:
        value: Value to validate
        validator: Validator to use
        field_name: Name for error messages

    Returns:
        Validated value

    Raises:
        ValidationError: If validation fails
    """
    return await validator.validate_async(value, field_name)


def validate_params(*param_validators: Tuple[str, ValidatorBase]):
    """
    Decorator to validate function parameters.

    Usage:
        @validate_params(
            ('name', Required() & Length(min=1, max=100)),
            ('email', Email()),
            ('age', Range(min=0, max=150))
        )
        def create_user(name: str, email: str, age: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Validate each parameter
            for param_name, validator in param_validators:
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    # validate() raises ValidationError on failure, returns value on success
                    bound.arguments[param_name] = validator.validate(value, param_name)

            return func(**bound.arguments)
        return wrapper
    return decorator


def validate_return(validator: ValidatorBase):
    """
    Decorator to validate function return value.

    Usage:
        @validate_return(TypeValidator(dict))
        def get_user(user_id: int) -> dict:
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # validate() raises ValidationError on failure, returns value on success
            validated_result = validator.validate(result, "return_value")
            return validated_result
        return wrapper
    return decorator


# Allow chaining validators with & operator
def _and_operator(self: ValidatorBase, other: ValidatorBase) -> 'And':
    """Allow using & to chain validators."""
    return And(self, other)


def _or_operator(self: ValidatorBase, other: ValidatorBase) -> 'Or':
    """Allow using | to chain validators."""
    return Or(self, other)


def _invert_operator(self: ValidatorBase) -> 'Not':
    """Allow using ~ to invert validators."""
    return Not(self)


# Monkey-patch the operators onto ValidatorBase
ValidatorBase.__and__ = _and_operator
ValidatorBase.__or__ = _or_operator
ValidatorBase.__invert__ = _invert_operator


__all__ = [
    "ValidationError",
    "ValidatorBase",
    "Required",
    "TypeValidator",
    "Range",
    "Length",
    "Pattern",
    "Email",
    "URL",
    "Custom",
    "And",
    "Or",
    "Not",
    "Schema",
    "PydanticValidator",
    "validate_args",
    "validate",
    "validate_async",
    "validate_params",
    "validate_return",
]
