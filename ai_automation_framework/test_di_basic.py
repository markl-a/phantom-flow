"""Basic test to demonstrate DI container functionality."""

from ai_automation_framework.core.di import Container, Lifetime, CircularDependencyError, ResolutionError
from typing import Protocol


# Define some test interfaces and classes
class ILogger(Protocol):
    """Logger interface."""
    def log(self, message: str) -> None:
        ...


class ConsoleLogger:
    """Console logger implementation."""
    def log(self, message: str) -> None:
        print(f"LOG: {message}")


class IDatabase(Protocol):
    """Database interface."""
    def query(self, sql: str, params: tuple = ()) -> str:
        ...


class MySQLDatabase:
    """MySQL database implementation."""
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.logger.log("MySQLDatabase initialized")

    def query(self, sql: str, params: tuple = ()) -> str:
        """Execute a parameterized query safely."""
        self.logger.log(f"Executing query: {sql} with params: {params}")
        return "Result"


class UserService:
    """Service that depends on database and logger."""
    def __init__(self, database: IDatabase, logger: ILogger):
        self.database = database
        self.logger = logger
        self.logger.log("UserService initialized")

    def get_user(self, user_id: int) -> str:
        # Use parameterized query to prevent SQL injection
        return self.database.query("SELECT * FROM users WHERE id = ?", (user_id,))


def test_basic_registration_and_resolution():
    """Test basic registration and resolution."""
    print("\n=== Test 1: Basic Registration and Resolution ===")
    container = Container()

    # Register logger as singleton
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)

    # Resolve logger
    logger1 = container.resolve(ILogger)
    logger2 = container.resolve(ILogger)

    logger1.log("Test message")

    # Verify singleton
    assert logger1 is logger2, "Singleton should return same instance"
    print("✓ Singleton works correctly")


def test_constructor_injection():
    """Test constructor injection with type hints."""
    print("\n=== Test 2: Constructor Injection ===")
    container = Container()

    # Register dependencies
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IDatabase, MySQLDatabase, Lifetime.TRANSIENT)

    # Resolve database - logger should be automatically injected
    db = container.resolve(IDatabase)
    result = db.query("SELECT 1")

    print("✓ Constructor injection works correctly")


def test_factory_function():
    """Test factory function registration."""
    print("\n=== Test 3: Factory Function ===")
    container = Container()

    # Register with factory
    container.register_factory(
        ILogger,
        lambda c: ConsoleLogger(),
        Lifetime.SINGLETON
    )

    logger = container.resolve(ILogger)
    logger.log("Factory created logger")

    print("✓ Factory function works correctly")


def test_named_registration():
    """Test named registration."""
    print("\n=== Test 4: Named Registration ===")
    container = Container()

    # Register multiple implementations with names
    logger1 = ConsoleLogger()
    logger2 = ConsoleLogger()

    container.register_instance(ILogger, logger1, name="primary")
    container.register_instance(ILogger, logger2, name="secondary")

    # Resolve by name
    primary = container.resolve(ILogger, name="primary")
    secondary = container.resolve(ILogger, name="secondary")

    assert primary is logger1, "Should resolve primary logger"
    assert secondary is logger2, "Should resolve secondary logger"

    print("✓ Named registration works correctly")


def test_lazy_resolution():
    """Test lazy resolution."""
    print("\n=== Test 5: Lazy Resolution ===")
    container = Container()

    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)

    # Create lazy proxy
    lazy_logger = container.resolve_lazy(ILogger)
    print("Lazy proxy created (not resolved yet)")

    # Use the proxy - this triggers resolution
    lazy_logger.log("Lazy resolution triggered")

    print("✓ Lazy resolution works correctly")


def test_scoped_lifetime():
    """Test scoped lifetime."""
    print("\n=== Test 6: Scoped Lifetime ===")
    container = Container()

    container.register(ILogger, ConsoleLogger, Lifetime.SCOPED)

    # Create scope
    with container.create_scope() as scope1:
        logger1a = scope1.resolve(ILogger)
        logger1b = scope1.resolve(ILogger)
        assert logger1a is logger1b, "Same instance within scope"

    with container.create_scope() as scope2:
        logger2 = scope2.resolve(ILogger)
        assert logger1a is not logger2, "Different instance in different scope"

    print("✓ Scoped lifetime works correctly")


def test_circular_dependency_detection():
    """Test circular dependency detection."""
    print("\n=== Test 7: Circular Dependency Detection ===")

    container = Container()

    # Register before defining to test circular deps
    # Note: We can't use forward references in local scope, so we'll simulate
    # circular dependency by using the resolution stack
    container.register(ILogger, ConsoleLogger)
    container.register(IDatabase, MySQLDatabase)

    # Now create a circular dependency by manually triggering resolution
    # This is a limitation of testing circular deps with locally defined classes
    # In real code, circular deps would be at module level where forward refs work

    # Instead, let's test the circular dependency detection directly
    # by checking the resolution stack
    try:
        # Simulate circular dependency by adding to stack
        test_key = (ILogger, None)
        container._resolution_stack.append(test_key)
        container.resolve(ILogger)
        assert False, "Should have raised CircularDependencyError"
    except CircularDependencyError as e:
        print(f"✓ Circular dependency detected: {e}")
    finally:
        container._resolution_stack.clear()


def test_complex_dependency_graph():
    """Test complex dependency graph with constructor injection."""
    print("\n=== Test 8: Complex Dependency Graph ===")
    container = Container()

    # Register all dependencies
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IDatabase, MySQLDatabase, Lifetime.TRANSIENT)
    container.register(UserService, UserService, Lifetime.TRANSIENT)

    # Resolve UserService - all dependencies should be automatically injected
    service = container.resolve(UserService)
    result = service.get_user(123)

    print("✓ Complex dependency graph works correctly")


if __name__ == "__main__":
    print("Running DI Container Tests...")
    print("=" * 60)

    test_basic_registration_and_resolution()
    test_constructor_injection()
    test_factory_function()
    test_named_registration()
    test_lazy_resolution()
    test_scoped_lifetime()
    test_circular_dependency_detection()
    test_complex_dependency_graph()

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
