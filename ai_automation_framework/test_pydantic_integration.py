"""
Example demonstrating Pydantic integration with the validation framework.
"""

try:
    from pydantic import BaseModel
    from ai_automation_framework.core.validation import (
        PydanticValidator,
        Schema,
        Required,
        TypeValidator,
    )

    class User(BaseModel):
        """Pydantic User model."""
        name: str
        age: int
        email: str

    print("Testing Pydantic Integration")
    print("=" * 60)

    # Create a Pydantic validator
    user_validator = PydanticValidator(User)

    # Valid data
    print("\n1. Valid Pydantic validation:")
    try:
        result = user_validator.validate({
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com"
        })
        print(f"   ✓ Validation passed: {result}")
        print(f"   Type: {type(result)}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    # Invalid data (wrong type)
    print("\n2. Invalid data (type mismatch):")
    try:
        user_validator.validate({
            "name": "Alice",
            "age": "not a number",  # Should be int
            "email": "alice@example.com"
        })
    except Exception as e:
        print(f"   ✓ Correctly caught error:")
        print(f"   {e}")

    # Mix Pydantic with other validators
    print("\n3. Combining Pydantic with Schema validation:")
    mixed_schema = Schema({
        "user": PydanticValidator(User),
        "active": Required() & TypeValidator(bool),
    })

    try:
        result = mixed_schema.validate({
            "user": {
                "name": "Bob",
                "age": 25,
                "email": "bob@example.com"
            },
            "active": True
        })
        print(f"   ✓ Mixed validation passed")
        print(f"   User type: {type(result['user'])}")
        print(f"   Active: {result['active']}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    print("\n" + "=" * 60)
    print("Pydantic integration test completed successfully!")
    print("=" * 60)

except ImportError:
    print("Pydantic is not installed. Skipping Pydantic integration test.")
    print("Install with: pip install pydantic")
