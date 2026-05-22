"""Dependency Injection Container for AI Automation Framework.

This module provides a comprehensive dependency injection (DI) system with support for
multiple dependency lifetimes, automatic constructor injection, factory functions,
named dependencies, lazy resolution, and scoped containers.

Key Features:
    - Three dependency lifetimes: SINGLETON, TRANSIENT, and SCOPED
    - Automatic constructor injection using type hints
    - Factory function support for complex object creation
    - Named dependencies for multiple implementations of the same interface
    - Lazy resolution with proxy objects
    - Child containers for scoped dependency management
    - Circular dependency detection
    - Thread-safe operations

Typical usage example:
    ```python
    from ai_automation_framework.core.di import Container, Lifetime

    # Create and configure container
    container = Container()
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IDatabase, MySQLDatabase, Lifetime.SCOPED)

    # Resolve dependencies
    logger = container.resolve(ILogger)

    # Use scoped containers
    with container.create_scope() as scope:
        db = scope.resolve(IDatabase)
        # Scoped instances are cleaned up on scope exit
    ```
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any, Callable, Dict, Generic, Optional, Type, TypeVar, Union,
    get_type_hints, get_origin, get_args
)
from threading import RLock
import inspect
import weakref


class Lifetime(Enum):
    """Dependency lifetime options for controlling instance creation and caching.

    Attributes:
        SINGLETON: One instance is created and shared across the entire container.
            The instance is cached and reused for all resolutions.
        TRANSIENT: A new instance is created every time the dependency is resolved.
            No caching occurs.
        SCOPED: One instance is created per scope (child container).
            The instance is cached within the scope and reused within that scope only.

    Example:
        ```python
        # Singleton - one instance for the entire application
        container.register(IConfig, AppConfig, Lifetime.SINGLETON)

        # Transient - new instance each time
        container.register(IRequest, HttpRequest, Lifetime.TRANSIENT)

        # Scoped - one instance per scope/request
        container.register(IDbContext, DatabaseContext, Lifetime.SCOPED)
        ```
    """
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


T = TypeVar('T')


class DIError(Exception):
    """Base exception for dependency injection errors.

    All DI-related exceptions inherit from this base class, allowing you to
    catch all DI errors with a single except clause.
    """
    pass


class CircularDependencyError(DIError):
    """Raised when circular dependencies are detected.

    This error occurs when a dependency chain forms a loop, such as:
    A depends on B, B depends on C, and C depends on A.

    Example:
        ```python
        class A:
            def __init__(self, b: 'B'):
                self.b = b

        class B:
            def __init__(self, a: A):
                self.a = a

        # This will raise CircularDependencyError
        container.register(A)
        container.register(B)
        container.resolve(A)  # Circular: A -> B -> A
        ```
    """
    pass


class ResolutionError(DIError):
    """Raised when a dependency cannot be resolved.

    This can occur when:
    - A service type is not registered
    - A required constructor parameter cannot be resolved
    - An error occurs during instance creation

    Example:
        ```python
        # Service not registered
        container.resolve(ILogger)  # ResolutionError: No registration found

        # Missing dependency
        class Service:
            def __init__(self, logger: ILogger):
                self.logger = logger

        container.register(Service)
        container.resolve(Service)  # ResolutionError: Cannot resolve ILogger
        ```
    """
    pass


class RegistrationError(DIError):
    """Raised when a dependency registration fails.

    This typically occurs when registration parameters are invalid or conflicting.

    Example:
        ```python
        # Invalid - providing both implementation and factory
        Registration(
            service_type=ILogger,
            implementation=ConsoleLogger,
            factory=lambda c: ConsoleLogger()  # Error!
        )
        ```
    """
    pass


class Registration:
    """Represents a dependency registration in the DI container.

    A registration defines how a service type should be resolved, including what
    implementation to use, how instances should be created, and their lifetime.

    Attributes:
        service_type (Type): The service type (interface or base class).
        implementation (Optional[Union[Type, Callable]]): The concrete implementation class.
        factory (Optional[Callable]): Factory function for creating instances.
        instance (Optional[Any]): Pre-created instance.
        lifetime (Lifetime): The lifetime of the dependency.
        name (Optional[str]): Optional name for named registration.

    Note:
        Exactly one of implementation, factory, or instance must be provided.
    """

    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Union[Type, Callable]] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: Lifetime = Lifetime.TRANSIENT,
        name: Optional[str] = None
    ):
        """Initialize a registration.

        Args:
            service_type (Type): The service type (interface or base class).
            implementation (Optional[Union[Type, Callable]]): The concrete implementation
                class. Defaults to None.
            factory (Optional[Callable]): Factory function for creating instances.
                Should accept a Container and return an instance. Defaults to None.
            instance (Optional[Any]): Pre-created instance to register. Defaults to None.
            lifetime (Lifetime): The lifetime of the dependency. Defaults to TRANSIENT.
            name (Optional[str]): Optional name for named registration. Allows multiple
                implementations of the same interface. Defaults to None.

        Raises:
            RegistrationError: If registration parameters are invalid (e.g., multiple
                or no creation methods provided).

        Example:
            ```python
            # Registration with implementation
            reg = Registration(
                service_type=ILogger,
                implementation=ConsoleLogger,
                lifetime=Lifetime.SINGLETON
            )

            # Registration with factory
            reg = Registration(
                service_type=IConfig,
                factory=lambda c: Config.from_file("config.json"),
                lifetime=Lifetime.SINGLETON
            )

            # Registration with instance
            logger = ConsoleLogger()
            reg = Registration(
                service_type=ILogger,
                instance=logger
            )
            ```
        """
        self.service_type = service_type
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        self.name = name

        # Validate registration
        if sum([implementation is not None, factory is not None, instance is not None]) != 1:
            raise RegistrationError(
                "Exactly one of implementation, factory, or instance must be provided"
            )


class LazyProxy(Generic[T]):
    """Lazy proxy for deferred dependency resolution.

    LazyProxy delays the resolution of a dependency until it's first accessed.
    This is useful for breaking circular dependencies, improving startup performance,
    or deferring expensive object creation.

    The proxy transparently forwards all attribute access and method calls to the
    underlying instance once it's resolved.

    Example:
        ```python
        # Create lazy proxy - no resolution yet
        logger = container.resolve_lazy(ILogger)

        # Resolution happens on first access
        logger.info("This triggers resolution")

        # Subsequent access uses cached instance
        logger.debug("This uses the cached instance")
        ```

    Note:
        The proxy only resolves the instance once. After the first resolution,
        the same instance is reused for all subsequent accesses.
    """

    def __init__(self, container: 'Container', service_type: Type[T], name: Optional[str] = None):
        """Initialize a lazy proxy.

        Args:
            container (Container): The DI container used for resolution.
            service_type (Type[T]): The service type to resolve.
            name (Optional[str]): Optional name for named resolution. Defaults to None.

        Example:
            ```python
            proxy = LazyProxy(container, ILogger)
            proxy_named = LazyProxy(container, ILogger, name="file")
            ```
        """
        self._container = container
        self._service_type = service_type
        self._name = name
        self._instance: Optional[T] = None
        self._resolved = False

    def _resolve(self) -> T:
        """Resolve the actual instance.

        Performs lazy resolution of the service on first call, then caches
        the result for subsequent calls.

        Returns:
            T: The resolved instance of the service.

        Raises:
            ResolutionError: If the service cannot be resolved.
            CircularDependencyError: If circular dependency is detected.
        """
        if not self._resolved:
            self._instance = self._container.resolve(self._service_type, self._name)
            self._resolved = True
        return self._instance

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the resolved instance.

        Args:
            name (str): The attribute name to access.

        Returns:
            Any: The attribute value from the resolved instance.

        Example:
            ```python
            logger = container.resolve_lazy(ILogger)
            level = logger.level  # Resolves and gets attribute
            ```
        """
        return getattr(self._resolve(), name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate method calls to the resolved instance.

        Args:
            *args: Positional arguments to pass to the resolved instance.
            **kwargs: Keyword arguments to pass to the resolved instance.

        Returns:
            Any: The return value from calling the resolved instance.

        Example:
            ```python
            factory = container.resolve_lazy(IFactory)
            result = factory.create("item")  # Resolves and calls
            ```
        """
        return self._resolve()(*args, **kwargs)


class Container:
    """
    Dependency Injection Container.

    Provides registration and resolution of dependencies with support for:
    - Multiple lifetimes (singleton, transient, scoped)
    - Constructor injection via type hints
    - Factory functions
    - Named dependencies
    - Lazy resolution
    - Child containers with scope isolation
    - Circular dependency detection

    Example:
        # Create container
        container = Container()

        # Register dependencies
        container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
        container.register(IDatabase, MySQLDatabase, Lifetime.SCOPED)

        # Register with factory
        container.register_factory(
            IConfig,
            lambda c: Config.from_file("config.json"),
            Lifetime.SINGLETON
        )

        # Resolve dependencies
        logger = container.resolve(ILogger)

        # Use scoped resolution
        with container.create_scope() as scope:
            db = scope.resolve(IDatabase)
            # db is disposed when scope exits
    """

    def __init__(self, parent: Optional['Container'] = None):
        """Initialize the container.

        Args:
            parent (Optional[Container]): Optional parent container for scoped resolution.
                When a child container cannot resolve a dependency, it delegates to its
                parent. Defaults to None.

        Example:
            ```python
            # Root container
            root = Container()

            # Child container with parent
            child = Container(parent=root)
            # Or use create_scope()
            child = root.create_scope()
            ```
        """
        self._registrations: Dict[tuple, Registration] = {}
        self._singletons: Dict[tuple, Any] = {}
        self._scoped_instances: Dict[tuple, Any] = {}
        self._lock = RLock()
        self._parent = parent
        self._resolution_stack: list = []

    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        lifetime: Lifetime = Lifetime.TRANSIENT,
        name: Optional[str] = None
    ) -> 'Container':
        """Register a service with its implementation.

        Args:
            service_type (Type[T]): The service type (interface or base class) to register.
            implementation (Optional[Type[T]]): The concrete implementation class.
                If None, service_type is used as both interface and implementation.
                Defaults to None.
            lifetime (Lifetime): The lifetime of the dependency (SINGLETON, TRANSIENT,
                or SCOPED). Defaults to TRANSIENT.
            name (Optional[str]): Optional name for named registration. Allows multiple
                implementations of the same interface. Defaults to None.

        Returns:
            Container: Self for method chaining.

        Example:
            ```python
            # Register with different interface and implementation
            container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)

            # Register class as both interface and implementation
            container.register(ConfigService, lifetime=Lifetime.SINGLETON)

            # Register named dependency
            container.register(IDatabase, MySQLDatabase, name="primary")
            container.register(IDatabase, PostgresDatabase, name="backup")
            ```
        """
        with self._lock:
            key = (service_type, name)
            registration = Registration(
                service_type=service_type,
                implementation=implementation or service_type,
                lifetime=lifetime,
                name=name
            )
            self._registrations[key] = registration
        return self

    def register_instance(
        self,
        service_type: Type[T],
        instance: T,
        name: Optional[str] = None
    ) -> 'Container':
        """Register a pre-created instance.

        This is useful for registering objects that are already created,
        configured, or obtained from external sources. The instance is
        treated as a singleton.

        Args:
            service_type (Type[T]): The service type to register the instance under.
            instance (T): The pre-created instance to register.
            name (Optional[str]): Optional name for named registration. Defaults to None.

        Returns:
            Container: Self for method chaining.

        Example:
            ```python
            # Register pre-configured instance
            logger = ConsoleLogger(level=LogLevel.DEBUG)
            container.register_instance(ILogger, logger)

            # Register named instance
            primary_db = MySQLDatabase(host="primary.db.com")
            container.register_instance(IDatabase, primary_db, name="primary")
            ```
        """
        with self._lock:
            key = (service_type, name)
            registration = Registration(
                service_type=service_type,
                instance=instance,
                lifetime=Lifetime.SINGLETON,
                name=name
            )
            self._registrations[key] = registration
            self._singletons[key] = instance
        return self

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[['Container'], T],
        lifetime: Lifetime = Lifetime.TRANSIENT,
        name: Optional[str] = None
    ) -> 'Container':
        """Register a factory function for creating instances.

        Factory functions provide full control over object creation. They receive
        the container as a parameter, allowing them to resolve dependencies manually
        or perform complex initialization logic.

        Args:
            service_type (Type[T]): The service type to register.
            factory (Callable[[Container], T]): Factory function that takes the
                container and returns an instance of the service.
            lifetime (Lifetime): The lifetime of the dependency. Defaults to TRANSIENT.
            name (Optional[str]): Optional name for named registration. Defaults to None.

        Returns:
            Container: Self for method chaining.

        Example:
            ```python
            # Factory with dependency resolution
            container.register_factory(
                ILogger,
                lambda c: ConsoleLogger(c.resolve(IConfig)),
                Lifetime.SINGLETON
            )

            # Factory with complex initialization
            def create_database(c: Container) -> IDatabase:
                config = c.resolve(IConfig)
                db = MySQLDatabase(
                    host=config.db_host,
                    port=config.db_port
                )
                db.connect()
                return db

            container.register_factory(IDatabase, create_database, Lifetime.SCOPED)
            ```
        """
        with self._lock:
            key = (service_type, name)
            registration = Registration(
                service_type=service_type,
                factory=factory,
                lifetime=lifetime,
                name=name
            )
            self._registrations[key] = registration
        return self

    def resolve(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """Resolve a dependency.

        Resolves a registered service type to an instance based on its registration
        and lifetime. Supports automatic constructor injection, circular dependency
        detection, and delegation to parent containers.

        Args:
            service_type (Type[T]): The service type to resolve.
            name (Optional[str]): Optional name for named resolution. When provided,
                resolves the named registration. Defaults to None.

        Returns:
            T: The resolved instance of the requested service type.

        Raises:
            ResolutionError: If the service type is not registered or dependencies
                cannot be resolved.
            CircularDependencyError: If a circular dependency is detected in the
                resolution chain.

        Example:
            ```python
            # Resolve unnamed service
            logger = container.resolve(ILogger)

            # Resolve named service
            primary_db = container.resolve(IDatabase, name="primary")
            backup_db = container.resolve(IDatabase, name="backup")

            # Automatic constructor injection
            class UserService:
                def __init__(self, logger: ILogger, db: IDatabase):
                    self.logger = logger
                    self.db = db

            container.register(UserService)
            service = container.resolve(UserService)  # Dependencies auto-injected
            ```
        """
        key = (service_type, name)

        # Check for circular dependency
        if key in self._resolution_stack:
            chain = " -> ".join([str(k[0].__name__) for k in self._resolution_stack])
            raise CircularDependencyError(
                f"Circular dependency detected: {chain} -> {service_type.__name__}"
            )

        try:
            self._resolution_stack.append(key)
            return self._resolve_internal(service_type, name)
        finally:
            self._resolution_stack.pop()

    def _resolve_internal(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """Internal resolution logic.

        Handles the core logic for resolving dependencies including registration lookup,
        parent delegation, and lifetime-based instance creation/retrieval.

        Args:
            service_type (Type[T]): The service type to resolve.
            name (Optional[str]): Optional name for named resolution. Defaults to None.

        Returns:
            T: The resolved instance.

        Raises:
            ResolutionError: If the service cannot be resolved (no registration found).
        """
        key = (service_type, name)

        # Check if registration exists
        registration = self._registrations.get(key)

        # If not found and no parent, try without name
        if registration is None and name is not None:
            registration = self._registrations.get((service_type, None))
            key = (service_type, None) if registration else key

        # If still not found, look in parent
        if registration is None and self._parent is not None:
            # Find registration in parent
            parent_registration = self._parent._find_registration(service_type, name)
            if parent_registration is not None:
                registration = parent_registration
                # For SINGLETON, delegate to parent to ensure single instance
                if registration.lifetime == Lifetime.SINGLETON:
                    return self._parent.resolve(service_type, name)
                # For SCOPED and TRANSIENT, resolve in current container

        # If still not found, raise error
        if registration is None:
            name_str = f" (name='{name}')" if name else ""
            raise ResolutionError(
                f"No registration found for {service_type.__name__}{name_str}"
            )

        # Handle different lifetimes
        if registration.lifetime == Lifetime.SINGLETON:
            return self._resolve_singleton(key, registration)
        elif registration.lifetime == Lifetime.SCOPED:
            return self._resolve_scoped(key, registration)
        else:  # TRANSIENT
            return self._create_instance(registration)

    def _find_registration(self, service_type: Type, name: Optional[str] = None) -> Optional[Registration]:
        """Find a registration in this container or parent containers.

        Searches for a registration in the current container and recursively
        searches parent containers if not found.

        Args:
            service_type (Type): The service type to find.
            name (Optional[str]): Optional name for named lookup. Defaults to None.

        Returns:
            Optional[Registration]: The registration if found, None otherwise.
        """
        key = (service_type, name)
        registration = self._registrations.get(key)

        if registration is None and name is not None:
            registration = self._registrations.get((service_type, None))

        if registration is None and self._parent is not None:
            return self._parent._find_registration(service_type, name)

        return registration

    def _resolve_singleton(self, key: tuple, registration: Registration) -> Any:
        """Resolve a singleton instance.

        Creates the singleton instance on first resolution and caches it for
        subsequent resolutions. Uses double-checked locking for thread safety.

        Args:
            key (tuple): The registration key (service_type, name).
            registration (Registration): The registration configuration.

        Returns:
            Any: The singleton instance.
        """
        # Check if already created
        if key in self._singletons:
            return self._singletons[key]

        # Create new singleton
        with self._lock:
            # Double-check after acquiring lock
            if key in self._singletons:
                return self._singletons[key]

            instance = self._create_instance(registration)
            self._singletons[key] = instance
            return instance

    def _resolve_scoped(self, key: tuple, registration: Registration) -> Any:
        """Resolve a scoped instance.

        Creates a scoped instance on first resolution within the scope and caches
        it for subsequent resolutions in the same scope. Uses double-checked locking
        for thread safety.

        Args:
            key (tuple): The registration key (service_type, name).
            registration (Registration): The registration configuration.

        Returns:
            Any: The scoped instance.
        """
        # Scoped instances are created once per container scope
        if key in self._scoped_instances:
            return self._scoped_instances[key]

        with self._lock:
            if key in self._scoped_instances:
                return self._scoped_instances[key]

            instance = self._create_instance(registration)
            self._scoped_instances[key] = instance
            return instance

    def _create_instance(self, registration: Registration) -> Any:
        """Create a new instance based on registration.

        Creates an instance using one of three methods: pre-created instance,
        factory function, or constructor injection.

        Args:
            registration (Registration): The registration configuration.

        Returns:
            Any: The created instance.

        Raises:
            ResolutionError: If instance creation fails.
        """
        # If instance is already provided
        if registration.instance is not None:
            return registration.instance

        # If factory is provided
        if registration.factory is not None:
            return registration.factory(self)

        # Use implementation with constructor injection
        implementation = registration.implementation
        return self._inject_constructor(implementation)

    def _inject_constructor(self, cls: Type[T]) -> T:
        """Create instance with constructor injection based on type hints.

        Analyzes the constructor signature, extracts type hints, resolves
        dependencies, and creates an instance with all dependencies injected.
        Handles optional parameters, forward references, and Union types.

        Args:
            cls (Type[T]): The class to instantiate.

        Returns:
            T: The created instance with injected dependencies.

        Raises:
            ResolutionError: If required dependencies cannot be resolved or
                instance creation fails.

        Example:
            ```python
            class UserService:
                def __init__(self, logger: ILogger, db: IDatabase):
                    self.logger = logger
                    self.db = db

            # Container automatically resolves ILogger and IDatabase
            service = container._inject_constructor(UserService)
            ```
        """
        try:
            # Get constructor signature
            sig = inspect.signature(cls.__init__)

            # Try to get type hints, but handle forward references
            try:
                type_hints = get_type_hints(cls.__init__)
            except (NameError, AttributeError):
                # If forward references can't be resolved, use raw annotations
                type_hints = getattr(cls.__init__, '__annotations__', {})

            # Build constructor arguments
            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Skip if has default value
                if param.default != inspect.Parameter.empty:
                    continue

                # Get type hint
                param_type = type_hints.get(param_name)
                if param_type is None:
                    continue

                # Handle string annotations (forward references)
                if isinstance(param_type, str):
                    # Try to resolve the string to a type safely (without eval)
                    try:
                        # Get the class's module namespace
                        module = inspect.getmodule(cls)
                        namespace = vars(module) if module else {}
                        # Safely lookup the type by name from the namespace
                        # This avoids using eval() which is a security risk
                        if param_type in namespace:
                            param_type = namespace[param_type]
                        elif hasattr(__builtins__, param_type) if isinstance(__builtins__, dict) else hasattr(__builtins__, param_type):
                            # Check if it's a builtin type
                            param_type = getattr(__builtins__, param_type) if isinstance(__builtins__, dict) else __builtins__.__dict__.get(param_type)
                        else:
                            # Can't resolve forward reference safely, skip
                            continue
                    except (NameError, AttributeError, TypeError):
                        # Can't resolve forward reference, skip this parameter
                        continue

                # Check if it's an Optional type
                origin = get_origin(param_type)
                if origin is Union:
                    args = get_args(param_type)
                    if type(None) in args:
                        # It's Optional, try to resolve but skip if not found
                        non_none_types = [t for t in args if t != type(None)]
                        if non_none_types:
                            try:
                                kwargs[param_name] = self.resolve(non_none_types[0])
                            except ResolutionError:
                                pass
                        continue

                # Resolve dependency
                try:
                    kwargs[param_name] = self.resolve(param_type)
                except ResolutionError as e:
                    raise ResolutionError(
                        f"Cannot resolve parameter '{param_name}' of type "
                        f"{param_type} for {cls.__name__}: {str(e)}"
                    )

            # Create instance
            return cls(**kwargs)

        except Exception as e:
            if isinstance(e, (ResolutionError, CircularDependencyError)):
                raise
            raise ResolutionError(
                f"Failed to create instance of {cls.__name__}: {str(e)}"
            )

    def resolve_lazy(self, service_type: Type[T], name: Optional[str] = None) -> LazyProxy[T]:
        """Create a lazy proxy for deferred resolution.

        Returns a proxy object that delays dependency resolution until the first
        time the object is accessed. This is useful for breaking circular dependencies,
        improving startup time, or deferring expensive initialization.

        Args:
            service_type (Type[T]): The service type to resolve lazily.
            name (Optional[str]): Optional name for named resolution. Defaults to None.

        Returns:
            LazyProxy[T]: A lazy proxy that resolves on first access.

        Example:
            ```python
            # Create lazy proxy - no resolution happens yet
            logger = container.resolve_lazy(ILogger)

            # Resolution happens on first access
            logger.info("Now it's resolved")

            # Subsequent calls use cached instance
            logger.debug("Uses same instance")

            # Useful for circular dependencies
            class A:
                def __init__(self, b: LazyProxy['B']):
                    self.b = b

            class B:
                def __init__(self, a: A):
                    self.a = a

            container.register(A)
            container.register(B)
            # Use lazy proxy to break the cycle
            ```
        """
        return LazyProxy(self, service_type, name)

    def create_scope(self) -> 'Container':
        """Create a child container for scoped resolution.

        Creates a new child container that inherits all registrations from its parent.
        SCOPED dependencies are created once per scope and cleaned up when the scope
        exits. SINGLETON dependencies are shared with the parent. TRANSIENT dependencies
        are created fresh each time.

        Returns:
            Container: A new child container with this container as parent.

        Example:
            ```python
            # Basic scoped usage
            with container.create_scope() as scope:
                service = scope.resolve(IScopedService)
                # Scoped instances are cleaned up on scope exit

            # Multiple scopes are isolated
            with container.create_scope() as scope1:
                db1 = scope1.resolve(IDatabase)  # Creates scoped instance

            with container.create_scope() as scope2:
                db2 = scope2.resolve(IDatabase)  # Creates new scoped instance

            # Useful for request-scoped dependencies in web applications
            def handle_request():
                with container.create_scope() as request_scope:
                    handler = request_scope.resolve(IRequestHandler)
                    handler.process()
            ```
        """
        return Container(parent=self)

    def is_registered(self, service_type: Type, name: Optional[str] = None) -> bool:
        """Check if a service is registered.

        Checks if a service type is registered in this container or any parent
        container. Useful for conditional resolution or validation.

        Args:
            service_type (Type): The service type to check.
            name (Optional[str]): Optional name to check for named registrations.
                Defaults to None.

        Returns:
            bool: True if the service is registered, False otherwise.

        Example:
            ```python
            # Check before resolving
            if container.is_registered(ILogger):
                logger = container.resolve(ILogger)
            else:
                logger = DefaultLogger()

            # Check named registration
            if container.is_registered(IDatabase, name="primary"):
                db = container.resolve(IDatabase, name="primary")

            # Validation
            required_services = [ILogger, IDatabase, ICache]
            missing = [s for s in required_services if not container.is_registered(s)]
            if missing:
                raise ValueError(f"Missing registrations: {missing}")
            ```
        """
        key = (service_type, name)
        if key in self._registrations:
            return True
        if self._parent is not None:
            return self._parent.is_registered(service_type, name)
        return False

    def clear(self) -> None:
        """Clear all registrations and cached instances.

        Removes all registrations and clears all cached singleton and scoped instances.
        This effectively resets the container to its initial empty state.

        Warning:
            This will remove all registrations and clear singleton/scoped caches.
            Use with caution as it will affect all code using this container.

        Example:
            ```python
            # Register services
            container.register(ILogger, ConsoleLogger)
            container.register(IDatabase, MySQLDatabase)

            # Clear everything
            container.clear()

            # Container is now empty
            assert not container.is_registered(ILogger)

            # Useful for testing
            def test_something():
                container.clear()  # Start with clean state
                container.register(ILogger, MockLogger)
                # ... test code ...
            ```
        """
        with self._lock:
            self._registrations.clear()
            self._singletons.clear()
            self._scoped_instances.clear()

    def __enter__(self) -> 'Container':
        """Context manager entry.

        Returns:
            Container: Self, allowing the container to be used with 'with' statements.

        Example:
            ```python
            with container.create_scope() as scope:
                service = scope.resolve(IScopedService)
            ```
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - clears scoped instances.

        Cleans up all scoped instances when exiting the context. This ensures
        proper resource cleanup for scoped dependencies.

        Args:
            exc_type: The exception type if an exception occurred.
            exc_val: The exception value if an exception occurred.
            exc_tb: The exception traceback if an exception occurred.

        Example:
            ```python
            with container.create_scope() as scope:
                db = scope.resolve(IDatabase)  # Scoped instance created
                # Use db...
            # db and other scoped instances are now cleaned up
            ```
        """
        self._scoped_instances.clear()


# Convenience function for creating a global container
_global_container: Optional[Container] = None


def get_global_container() -> Container:
    """Get or create the global container instance.

    Returns a singleton container instance that can be used throughout the
    application. This is convenient for simple applications but consider using
    explicit container passing for better testability.

    Returns:
        Container: The global container instance.

    Example:
        ```python
        # Get global container and configure
        container = get_global_container()
        container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
        container.register(IDatabase, MySQLDatabase, Lifetime.SCOPED)

        # Access from anywhere in the application
        def some_function():
            container = get_global_container()
            logger = container.resolve(ILogger)
            logger.info("Using global container")

        # Better for simple applications
        get_global_container().register(IConfig, AppConfig)
        ```

    Note:
        While convenient, global containers can make testing harder. Consider
        passing containers explicitly for better dependency management.
    """
    global _global_container
    if _global_container is None:
        _global_container = Container()
    return _global_container


def reset_global_container() -> None:
    """Reset the global container.

    Clears the global container reference, causing the next call to
    get_global_container() to create a new container instance.

    This is useful for testing to ensure a clean state between tests,
    or for reinitializing the application.

    Example:
        ```python
        # In test setup
        def setup():
            reset_global_container()
            container = get_global_container()
            # Register test dependencies
            container.register(ILogger, MockLogger)

        # Reinitialize application
        def restart_app():
            reset_global_container()
            container = get_global_container()
            # Register fresh dependencies
            setup_dependencies(container)

        # Test isolation
        def test_service_a():
            reset_global_container()
            # Test with clean container
            pass

        def test_service_b():
            reset_global_container()
            # Test with clean container
            pass
        ```
    """
    global _global_container
    _global_container = None
