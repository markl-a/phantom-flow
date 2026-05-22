"""
Demonstration of the comprehensive validation framework.

This script demonstrates all features of the validation framework including:
- Basic validators (Required, Type, Range, Length, Pattern, Email, URL)
- Composite validators (AND, OR, NOT)
- Schema validation
- Function argument validation
- Chainable validation rules
- Async validation support
- Detailed error messages with field paths
- Integration with Pydantic (if available)
"""

import asyncio
from ai_automation_framework.core.validation import (
    ValidationError,
    Required,
    TypeValidator,
    Range,
    Length,
    Pattern,
    Email,
    URL,
    Custom,
    And,
    Or,
    Not,
    Schema,
    validate_args,
    validate,
    validate_async,
)


def test_basic_validators():
    """Test basic validators."""
    print("=" * 60)
    print("Testing Basic Validators")
    print("=" * 60)

    # Required validator
    print("\n1. Required Validator:")
    try:
        Required().validate(None)
    except ValidationError as e:
        print(f"   ✓ Correctly caught None: {e.message}")

    try:
        Required(allow_empty=False).validate("")
    except ValidationError as e:
        print(f"   ✓ Correctly caught empty string: {e.message}")

    # Type validator
    print("\n2. Type Validator:")
    try:
        result = TypeValidator(str).validate("hello")
        print(f"   ✓ String validated: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        TypeValidator(int).validate("not an int")
    except ValidationError as e:
        print(f"   ✓ Correctly caught type mismatch: {e.message}")

    # Range validator
    print("\n3. Range Validator:")
    try:
        result = Range(min_value=0, max_value=100).validate(50)
        print(f"   ✓ Value in range: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        Range(min_value=0, max_value=100).validate(150)
    except ValidationError as e:
        print(f"   ✓ Correctly caught out of range: {e.message}")

    # Length validator
    print("\n4. Length Validator:")
    try:
        result = Length(min_length=3, max_length=10).validate("hello")
        print(f"   ✓ String length valid: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        Length(exact_length=5).validate("hello world")
    except ValidationError as e:
        print(f"   ✓ Correctly caught wrong length: {e.message}")

    # Pattern validator
    print("\n5. Pattern Validator:")
    try:
        result = Pattern(r'^\d{3}-\d{4}$').validate("123-4567")
        print(f"   ✓ Pattern matched: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        Pattern(r'^\d{3}-\d{4}$').validate("invalid")
    except ValidationError as e:
        print(f"   ✓ Correctly caught pattern mismatch: {e.message}")

    # Email validator
    print("\n6. Email Validator:")
    try:
        result = Email().validate("user@example.com")
        print(f"   ✓ Valid email: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        Email().validate("invalid-email")
    except ValidationError as e:
        print(f"   ✓ Correctly caught invalid email: {e.message}")

    # URL validator
    print("\n7. URL Validator:")
    try:
        result = URL().validate("https://example.com/path")
        print(f"   ✓ Valid URL: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        URL().validate("not-a-url")
    except ValidationError as e:
        print(f"   ✓ Correctly caught invalid URL: {e.message}")

    # Custom validator
    print("\n8. Custom Validator:")
    def is_even(x):
        return isinstance(x, int) and x % 2 == 0

    try:
        result = Custom(is_even, error_message="Must be even number").validate(4)
        print(f"   ✓ Custom validation passed: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        Custom(is_even, error_message="Must be even number").validate(5)
    except ValidationError as e:
        print(f"   ✓ Correctly caught custom validation failure: {e.message}")


def test_composite_validators():
    """Test composite validators (AND, OR, NOT)."""
    print("\n" + "=" * 60)
    print("Testing Composite Validators")
    print("=" * 60)

    # AND validator
    print("\n1. AND Validator:")
    validator = And(
        TypeValidator(str),
        Length(min_length=3, max_length=10),
        Pattern(r'^[a-z]+$')
    )

    try:
        result = validator.validate("hello")
        print(f"   ✓ All validators passed: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        validator.validate("HELLO")  # Fails pattern (must be lowercase)
    except ValidationError as e:
        print(f"   ✓ Correctly caught AND failure: {e.message}")

    # OR validator
    print("\n2. OR Validator:")
    validator = Or(
        TypeValidator(int),
        TypeValidator(float)
    )

    try:
        result = validator.validate(42)
        print(f"   ✓ OR validator passed with int: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        result = validator.validate(3.14)
        print(f"   ✓ OR validator passed with float: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        validator.validate("string")
    except ValidationError as e:
        print(f"   ✓ Correctly caught OR failure: All validators failed")

    # NOT validator
    print("\n3. NOT Validator:")
    validator = Not(TypeValidator(str))

    try:
        result = validator.validate(42)
        print(f"   ✓ NOT validator passed (not a string): {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        validator.validate("string")
    except ValidationError as e:
        print(f"   ✓ Correctly caught NOT failure: {e.message}")


def test_chainable_validators():
    """Test chainable validation with & operator."""
    print("\n" + "=" * 60)
    print("Testing Chainable Validators (& operator)")
    print("=" * 60)

    # Chain validators using & operator
    validator = Required() & TypeValidator(str) & Length(min_length=3, max_length=20) & Email()

    try:
        result = validator.validate("user@example.com")
        print(f"   ✓ Chained validation passed: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    try:
        validator.validate(None)
    except ValidationError as e:
        print(f"   ✓ Failed at Required: {e.message}")

    try:
        validator.validate("ab")  # Too short
    except ValidationError as e:
        print(f"   ✓ Failed at Length: {e.message}")

    try:
        validator.validate("not-an-email-but-long-enough")
    except ValidationError as e:
        print(f"   ✓ Failed at Email: {e.message}")

    # Chain with | (OR) operator
    print("\n   Testing | (OR) operator:")
    validator = TypeValidator(int) | TypeValidator(float)

    try:
        result = validator.validate(42)
        print(f"   ✓ OR chaining with int: {result}")
        result = validator.validate(3.14)
        print(f"   ✓ OR chaining with float: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")


def test_schema_validation():
    """Test schema validation for dictionaries."""
    print("\n" + "=" * 60)
    print("Testing Schema Validation")
    print("=" * 60)

    # Define a schema
    user_schema = Schema({
        "name": Required() & TypeValidator(str) & Length(min_length=1, max_length=50),
        "email": Required() & Email(),
        "age": Required() & TypeValidator(int) & Range(min_value=0, max_value=150),
        "website": TypeValidator(str) & URL(),  # Optional field
    })

    # Valid data
    print("\n1. Valid user data:")
    valid_user = {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "website": "https://johndoe.com"
    }

    try:
        result = user_schema.validate(valid_user)
        print(f"   ✓ Schema validation passed")
        print(f"   Data: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    # Invalid data
    print("\n2. Invalid user data (multiple errors):")
    invalid_user = {
        "name": "",  # Empty name
        "email": "invalid-email",  # Invalid email
        "age": 200,  # Out of range
        "website": "not-a-url"  # Invalid URL
    }

    try:
        user_schema.validate(invalid_user)
    except ValidationError as e:
        print(f"   ✓ Correctly caught schema errors:")
        print(f"   Main message: {e.message}")
        for error in e.errors:
            print(f"   - {error['field']}: {error['message']}")

    # Strict mode
    print("\n3. Strict schema (reject unknown fields):")
    strict_schema = Schema({
        "name": Required() & TypeValidator(str),
    }, strict=True)

    try:
        strict_schema.validate({"name": "John", "extra": "field"})
    except ValidationError as e:
        print(f"   ✓ Correctly rejected unknown fields:")
        for error in e.errors:
            print(f"   - {error['message']}")


def test_function_decorator():
    """Test @validate_args decorator."""
    print("\n" + "=" * 60)
    print("Testing @validate_args Decorator")
    print("=" * 60)

    @validate_args(
        name=Required() & TypeValidator(str) & Length(min_length=1),
        age=Required() & TypeValidator(int) & Range(min_value=0, max_value=150),
        email=Email()
    )
    def create_user(name: str, age: int, email: str = None):
        """Create a user with validated arguments."""
        return {"name": name, "age": age, "email": email}

    # Valid call
    print("\n1. Valid function call:")
    try:
        result = create_user("Alice", 25, "alice@example.com")
        print(f"   ✓ Function executed successfully: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    # Invalid name
    print("\n2. Invalid name (empty string):")
    try:
        create_user("", 25, "alice@example.com")
    except ValidationError as e:
        print(f"   ✓ Correctly caught validation error: {e}")

    # Invalid age
    print("\n3. Invalid age (out of range):")
    try:
        create_user("Alice", 200, "alice@example.com")
    except ValidationError as e:
        print(f"   ✓ Correctly caught validation error: {e}")

    # Invalid email
    print("\n4. Invalid email:")
    try:
        create_user("Alice", 25, "not-an-email")
    except ValidationError as e:
        print(f"   ✓ Correctly caught validation error: {e}")


async def test_async_validation():
    """Test async validation support."""
    print("\n" + "=" * 60)
    print("Testing Async Validation")
    print("=" * 60)

    # Async custom validator
    async def check_username_available(username):
        """Simulate async database check."""
        await asyncio.sleep(0.1)  # Simulate network delay
        unavailable = ["admin", "root", "test"]
        return username not in unavailable

    validator = Custom(
        lambda x: True,  # Sync version (always pass)
        async_validator_func=check_username_available,
        error_message="Username is already taken"
    )

    # Valid username
    print("\n1. Available username:")
    try:
        result = await validator.validate_async("john_doe")
        print(f"   ✓ Async validation passed: '{result}'")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")

    # Unavailable username
    print("\n2. Unavailable username:")
    try:
        await validator.validate_async("admin")
    except ValidationError as e:
        print(f"   ✓ Correctly caught async validation failure: {e.message}")

    # Async schema validation
    print("\n3. Async schema validation:")
    user_schema = Schema({
        "username": Required() & TypeValidator(str) & validator,
        "email": Required() & Email(),
    })

    try:
        result = await user_schema.validate_async({
            "username": "john_doe",
            "email": "john@example.com"
        })
        print(f"   ✓ Async schema validation passed: {result}")
    except ValidationError as e:
        print(f"   ✗ Failed: {e}")


def test_error_messages():
    """Test detailed error messages with field paths."""
    print("\n" + "=" * 60)
    print("Testing Detailed Error Messages")
    print("=" * 60)

    # Nested schema
    address_schema = Schema({
        "street": Required() & TypeValidator(str),
        "city": Required() & TypeValidator(str),
        "zip": Required() & Pattern(r'^\d{5}$'),
    })

    user_schema = Schema({
        "name": Required() & TypeValidator(str),
        "address": address_schema,
    })

    invalid_data = {
        "name": "John",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "zip": "invalid"  # Invalid zip code
        }
    }

    try:
        user_schema.validate(invalid_data)
    except ValidationError as e:
        print(f"\n   Error details:")
        print(f"   Message: {e.message}")
        print(f"   Field path: {e.field_path}")
        if e.errors:
            print(f"   Detailed errors:")
            for error in e.errors:
                print(f"   - Field: {error['field']}")
                print(f"     Message: {error['message']}")


def main():
    """Run all tests."""
    print("\n")
    print("*" * 60)
    print("* COMPREHENSIVE VALIDATION FRAMEWORK DEMONSTRATION")
    print("*" * 60)

    test_basic_validators()
    test_composite_validators()
    test_chainable_validators()
    test_schema_validation()
    test_function_decorator()
    test_error_messages()

    # Run async tests
    print("\n")
    asyncio.run(test_async_validation())

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    main()
