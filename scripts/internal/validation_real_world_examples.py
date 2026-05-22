"""
Real-world examples using the validation framework.

This demonstrates practical use cases:
1. API request validation
2. Configuration file validation
3. Database model validation
4. Form data validation
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
    Schema,
    validate_args,
)


# ============================================================
# Example 1: API Request Validation
# ============================================================

# Define API request schemas
create_user_schema = Schema({
    "username": Required() & TypeValidator(str) & Length(min_length=3, max_length=20) & Pattern(r'^[a-zA-Z0-9_]+$'),
    "email": Required() & Email(),
    "password": Required() & TypeValidator(str) & Length(min_length=8, max_length=100),
    "age": TypeValidator(int) & Range(min_value=13, max_value=120),  # Optional
    "website": URL(),  # Optional
}, strict=True)

def handle_create_user_request(request_data: dict):
    """Handle API request to create a user."""
    try:
        validated_data = create_user_schema.validate(request_data)
        print(f"✓ Valid user creation request: {validated_data['username']}")
        return {"status": "success", "user": validated_data}
    except ValidationError as e:
        print(f"✗ Invalid request:")
        for error in e.errors:
            print(f"  - {error['field']}: {error['message']}")
        return {"status": "error", "errors": e.errors}


# ============================================================
# Example 2: Configuration File Validation
# ============================================================

# Database configuration schema
db_config_schema = Schema({
    "host": Required() & TypeValidator(str),
    "port": Required() & TypeValidator(int) & Range(min_value=1, max_value=65535),
    "database": Required() & TypeValidator(str) & Length(min_length=1),
    "username": Required() & TypeValidator(str),
    "password": Required() & TypeValidator(str),
    "pool_size": TypeValidator(int) & Range(min_value=1, max_value=100),
    "timeout": TypeValidator(int) & Range(min_value=1, max_value=300),
})

# Application configuration schema
app_config_schema = Schema({
    "app_name": Required() & TypeValidator(str),
    "debug": Required() & TypeValidator(bool),
    "database": db_config_schema,
    "api_key": Required() & TypeValidator(str) & Length(exact_length=32),
    "log_level": Required() & Custom(
        lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR"],
        error_message="Must be one of: DEBUG, INFO, WARNING, ERROR"
    ),
})

def validate_config(config: dict):
    """Validate application configuration."""
    try:
        validated = app_config_schema.validate(config)
        print("✓ Configuration is valid")
        return validated
    except ValidationError as e:
        print("✗ Configuration errors:")
        for error in e.errors:
            print(f"  - {error['field']}: {error['message']}")
        raise


# ============================================================
# Example 3: Function Argument Validation with Decorator
# ============================================================

@validate_args(
    title=Required() & TypeValidator(str) & Length(min_length=1, max_length=200),
    content=Required() & TypeValidator(str) & Length(min_length=10),
    tags=TypeValidator(list),
    published=TypeValidator(bool)
)
def create_blog_post(title: str, content: str, tags: list = None, published: bool = False):
    """Create a blog post with validated arguments."""
    post = {
        "title": title,
        "content": content,
        "tags": tags or [],
        "published": published
    }
    print(f"✓ Blog post created: '{title}'")
    return post


# ============================================================
# Example 4: Complex Validation Rules
# ============================================================

# Password strength validator
def is_strong_password(password):
    """Check if password meets strength requirements."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    return has_upper and has_lower and has_digit and has_special

password_validator = (
    Required() &
    TypeValidator(str) &
    Length(min_length=8, max_length=100) &
    Custom(is_strong_password, error_message="Password must contain uppercase, lowercase, digit, and special character")
)

# Credit card validation (Luhn algorithm)
def luhn_check(card_number):
    """Validate credit card number using Luhn algorithm."""
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10 == 0

credit_card_validator = (
    Required() &
    TypeValidator(str) &
    Pattern(r'^\d{13,19}$') &
    Custom(luhn_check, error_message="Invalid credit card number")
)


# ============================================================
# Example 5: Async Validation for External Checks
# ============================================================

async def check_email_exists(email):
    """Simulate async check if email exists in database."""
    await asyncio.sleep(0.1)  # Simulate database query
    existing_emails = ["admin@example.com", "test@example.com"]
    return email not in existing_emails

email_availability_validator = Email() & Custom(
    lambda x: True,  # Sync version (basic validation)
    async_validator_func=check_email_exists,
    error_message="Email already exists"
)

async def register_user_async(email: str):
    """Register user with async email validation."""
    try:
        validated_email = await email_availability_validator.validate_async(email)
        print(f"✓ Email is available: {validated_email}")
        return {"status": "success", "email": validated_email}
    except ValidationError as e:
        print(f"✗ Email validation failed: {e.message}")
        return {"status": "error", "message": e.message}


# ============================================================
# Main Demonstration
# ============================================================

def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("REAL-WORLD VALIDATION EXAMPLES")
    print("=" * 70)

    # Example 1: API Request Validation
    print("\n1. API Request Validation")
    print("-" * 70)

    valid_request = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "age": 25
    }
    handle_create_user_request(valid_request)

    invalid_request = {
        "username": "ab",  # Too short
        "email": "invalid-email",
        "password": "weak",  # Too short
        "extra_field": "not allowed"  # Unknown field (strict mode)
    }
    handle_create_user_request(invalid_request)

    # Example 2: Configuration Validation
    print("\n2. Configuration File Validation")
    print("-" * 70)

    valid_config = {
        "app_name": "MyApp",
        "debug": True,
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "mydb",
            "username": "user",
            "password": "pass",
            "pool_size": 10,
            "timeout": 30
        },
        "api_key": "12345678901234567890123456789012",  # 32 chars
        "log_level": "INFO"
    }

    try:
        validate_config(valid_config)
    except ValidationError:
        pass

    invalid_config = {
        "app_name": "MyApp",
        "debug": True,
        "database": {
            "host": "localhost",
            "port": 99999,  # Invalid port
            "database": "",  # Empty database name
            "username": "user",
            "password": "pass"
        },
        "api_key": "short",  # Wrong length
        "log_level": "INVALID"  # Invalid log level
    }

    try:
        validate_config(invalid_config)
    except ValidationError:
        pass

    # Example 3: Function Decorator
    print("\n3. Function Argument Validation")
    print("-" * 70)

    try:
        create_blog_post(
            title="My First Post",
            content="This is a great blog post with enough content.",
            tags=["python", "validation"],
            published=True
        )
    except ValidationError as e:
        print(f"✗ Error: {e}")

    try:
        create_blog_post(
            title="",  # Empty title
            content="Short",  # Too short
        )
    except ValidationError as e:
        print(f"✗ Error: {e}")

    # Example 4: Complex Validators
    print("\n4. Complex Validation Rules")
    print("-" * 70)

    print("Testing password strength:")
    try:
        password_validator.validate("WeakPass")
    except ValidationError as e:
        print(f"  ✗ Weak password rejected: {e.message}")

    try:
        result = password_validator.validate("Strong123!Pass")
        print(f"  ✓ Strong password accepted: {result}")
    except ValidationError as e:
        print(f"  ✗ Error: {e}")

    print("\nTesting credit card:")
    try:
        credit_card_validator.validate("1234567890123456")  # Invalid
    except ValidationError as e:
        print(f"  ✗ Invalid card rejected: {e.message}")

    try:
        # Valid test card number
        result = credit_card_validator.validate("4532015112830366")
        print(f"  ✓ Valid card accepted: {result}")
    except ValidationError as e:
        print(f"  ✗ Error: {e}")

    # Example 5: Async Validation
    print("\n5. Async Validation")
    print("-" * 70)

    async def run_async_tests():
        await register_user_async("newuser@example.com")  # Available
        await register_user_async("admin@example.com")  # Already exists

    asyncio.run(run_async_tests())

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
