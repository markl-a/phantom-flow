# Validation Framework Quick Start Guide

## Overview

The AI Automation Framework now includes a comprehensive data validation framework with:
- Built-in validators (Required, Type, Range, Length, Pattern, Email, URL, Custom)
- Composite validators (AND, OR, NOT)
- Schema validation for dictionaries
- Function argument validation decorators
- Async validation support
- Pydantic integration
- Detailed error messages with field paths

## Installation

The validation framework is already integrated into the core framework:

```python
from ai_automation_framework.core import (
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
    PydanticValidator,
    validate_args,
    validate,
    validate_async,
)
```

## Quick Examples

### 1. Basic Validation

```python
from ai_automation_framework.core import Required, TypeValidator, Email

# Simple validation
email_validator = Required() & TypeValidator(str) & Email()

try:
    validated_email = email_validator.validate("user@example.com")
    print(f"Valid email: {validated_email}")
except ValidationError as e:
    print(f"Error: {e.message}")
```

### 2. Chainable Validators (& operator)

```python
from ai_automation_framework.core import Required, TypeValidator, Length, Pattern

# Chain validators together
username_validator = (
    Required() &
    TypeValidator(str) &
    Length(min_length=3, max_length=20) &
    Pattern(r'^[a-zA-Z0-9_]+$')
)

# Validate
username = username_validator.validate("john_doe")
```

### 3. Schema Validation

```python
from ai_automation_framework.core import Schema, Required, TypeValidator, Email, Range

# Define schema
user_schema = Schema({
    "name": Required() & TypeValidator(str) & Length(min_length=1),
    "email": Required() & Email(),
    "age": Required() & TypeValidator(int) & Range(min_value=0, max_value=150),
})

# Validate data
user_data = {
    "name": "Alice",
    "email": "alice@example.com",
    "age": 25
}

try:
    validated = user_schema.validate(user_data)
except ValidationError as e:
    print(f"Validation errors: {e.errors}")
```

### 4. Function Argument Validation

```python
from ai_automation_framework.core import validate_args, Required, TypeValidator, Range

@validate_args(
    title=Required() & TypeValidator(str) & Length(min_length=1, max_length=200),
    content=Required() & TypeValidator(str),
    priority=TypeValidator(int) & Range(min_value=1, max_value=5)
)
def create_task(title: str, content: str, priority: int = 3):
    return {"title": title, "content": content, "priority": priority}

# Use the function
task = create_task("My Task", "Task description", 1)
```

### 5. Composite Validators

```python
from ai_automation_framework.core import Or, And, Not, TypeValidator, Range

# OR: Accept int OR float
numeric_validator = TypeValidator(int) | TypeValidator(float)

# AND: Must satisfy all conditions
positive_number = TypeValidator(int) & Range(min_value=0)

# NOT: Invert validation
not_string = ~TypeValidator(str)
```

### 6. Custom Validators

```python
from ai_automation_framework.core import Custom

def is_even(x):
    return isinstance(x, int) and x % 2 == 0

even_validator = Custom(
    is_even,
    error_message="Value must be an even number"
)

# Validate
value = even_validator.validate(42)  # Passes
```

### 7. Async Validation

```python
import asyncio
from ai_automation_framework.core import Custom, Email

async def check_email_exists(email):
    # Simulate database check
    await asyncio.sleep(0.1)
    existing_emails = ["admin@example.com"]
    return email not in existing_emails

email_availability = Email() & Custom(
    lambda x: True,  # Sync fallback
    async_validator_func=check_email_exists,
    error_message="Email already exists"
)

# Use async validation
async def register_user(email):
    try:
        validated = await email_availability.validate_async(email)
        print(f"Email available: {validated}")
    except ValidationError as e:
        print(f"Error: {e.message}")

asyncio.run(register_user("newuser@example.com"))
```

### 8. Pydantic Integration

```python
from pydantic import BaseModel
from ai_automation_framework.core import PydanticValidator, Schema

class User(BaseModel):
    name: str
    age: int
    email: str

# Use Pydantic model as validator
user_validator = PydanticValidator(User)

# Validate
validated_user = user_validator.validate({
    "name": "Alice",
    "age": 30,
    "email": "alice@example.com"
})
# Returns: User instance
```

## Error Handling

```python
from ai_automation_framework.core import ValidationError, Schema, Required, Email

schema = Schema({
    "email": Required() & Email(),
    "age": Required() & TypeValidator(int)
})

try:
    schema.validate({"email": "invalid", "age": "not a number"})
except ValidationError as e:
    print(f"Message: {e.message}")
    print(f"Field path: {e.field_path}")
    print(f"Errors: {e.errors}")

    # Get errors as dict
    error_dict = e.to_dict()
```

## Built-in Validators

| Validator | Purpose | Example |
|-----------|---------|---------|
| `Required()` | Ensure value is not None/empty | `Required(allow_empty=False)` |
| `TypeValidator(type)` | Check value type | `TypeValidator(str)` |
| `Range(min, max)` | Validate numeric range | `Range(min_value=0, max_value=100)` |
| `Length(min, max)` | Validate length | `Length(min_length=3, max_length=20)` |
| `Pattern(regex)` | Match regex pattern | `Pattern(r'^\d{3}-\d{4}$')` |
| `Email()` | Validate email address | `Email()` |
| `URL()` | Validate URL | `URL(allowed_schemes={'http', 'https'})` |
| `Custom(func)` | Custom validation | `Custom(lambda x: x > 0)` |

## Composite Validators

| Validator | Purpose | Example |
|-----------|---------|---------|
| `And(*validators)` | All must pass | `And(TypeValidator(int), Range(0, 100))` |
| `Or(*validators)` | At least one must pass | `Or(TypeValidator(int), TypeValidator(float))` |
| `Not(validator)` | Invert result | `Not(TypeValidator(str))` |

## Operators

| Operator | Equivalent | Example |
|----------|------------|---------|
| `&` | `And(a, b)` | `Required() & TypeValidator(str)` |
| `\|` | `Or(a, b)` | `TypeValidator(int) \| TypeValidator(float)` |
| `~` | `Not(a)` | `~TypeValidator(str)` |

## Best Practices

1. **Chain validators for readability:**
   ```python
   validator = Required() & TypeValidator(str) & Length(min_length=3) & Email()
   ```

2. **Use schemas for complex data:**
   ```python
   user_schema = Schema({
       "name": Required() & TypeValidator(str),
       "email": Required() & Email(),
   })
   ```

3. **Add custom error messages:**
   ```python
   validator = Range(0, 100, error_message="Age must be between 0 and 100")
   ```

4. **Use strict mode for APIs:**
   ```python
   api_schema = Schema({...}, strict=True)  # Reject unknown fields
   ```

5. **Leverage async validation for I/O:**
   ```python
   async_validator = Custom(sync_func, async_validator_func=async_func)
   ```

## More Examples

See the example files:
- `test_validation_demo.py` - Comprehensive feature demonstration
- `test_pydantic_integration.py` - Pydantic integration
- `validation_real_world_examples.py` - Real-world use cases

## File Location

**Main file:** `/home/user/Automation_with_AI/ai_automation_framework/core/validation.py`

**Lines of code:** 1042

**Exports:** All validators are exported in `ai_automation_framework/core/__init__.py`
