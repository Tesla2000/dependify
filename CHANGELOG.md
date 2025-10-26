# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Lazy Evaluation Support

- **Evaluation Strategy Enum**: Added `EvaluationStrategy` enum with three strategies:
  - `EAGER` (default): Dependencies instantiated immediately at construction
  - `LAZY`: Dependencies instantiated on first access
  - `OPTIONAL_LAZY`: Dependencies instantiated on first access, returns `None` if not registered

- **Class-level Lazy Evaluation**: Classes can now specify evaluation strategy for all dependencies:
  ```python
  @injected(evaluation_strategy=EvaluationStrategy.LAZY)
  class Service:
      db: Database
      logger: Logger
  ```

- **Field-level Lazy Markers**: Individual fields can be marked for lazy evaluation using `Annotated`:
  - `Lazy` marker: Forces lazy evaluation for specific field
  - `OptionalLazy` marker: Lazy evaluation that returns `None` if dependency not registered
  ```python
  @injected  # class is EAGER by default
  class Service:
      db: Annotated[Database, Lazy]  # This field is lazy
      cache: Annotated[Cache, OptionalLazy]  # Optional lazy field
      logger: Logger  # This field is eager
  ```

- **Marker Constants**: Added type-safe marker constants to replace string-based annotations:
  - `Lazy`: Singleton marker for lazy field evaluation
  - `OptionalLazy`: Singleton marker for optional lazy field evaluation
  - `Eager`: Singleton marker for explicit eager field evaluation (useful when class is lazy but specific field should be eager)
  - All markers inherit from `Marker` base class for type checking
  - Markers are properly hashable and comparable

#### Infrastructure Changes

- **Property-based Lazy Implementation**:
  - `PropertyMaker`: Creates property descriptors for lazy dependencies
  - `OptionalPropertyMaker`: Creates property descriptors for optional lazy dependencies
  - Properties cache resolved values after first access

- **Creator Pattern**: Refactored class creation into specialized creators:
  - `EagerCreator`: Handles eager evaluation (immediate dependency resolution)
  - `LazyCreator`: Handles lazy evaluation (deferred dependency resolution)
  - `OptionalLazyCreator`: Handles optional lazy evaluation

- **Evaluation Strategy Module**: Centralized `EvaluationStrategy` enum definition in `_evaluation_strategy.py`

### Changed

- **`@injected` Decorator**: Now accepts `evaluation_strategy` parameter
- **`@wired` Decorator**: Now accepts `evaluation_strategy` parameter and passes it through to `@injected`
- **Module Exports**: Added `Lazy`, `OptionalLazy`, `Eager`, and `EvaluationStrategy` to public API exports

### Testing

#### Test Coverage Added

- **test_lazy.py** (14 tests): Comprehensive tests for `LAZY` evaluation strategy
  - Basic lazy vs eager comparison
  - Multiple lazy dependencies
  - Custom containers
  - Dependency caching
  - Manual overrides
  - Non-injectable fields
  - Default values
  - `@wired` decorator integration
  - `__post_init__` behavior
  - Class inheritance
  - Multiple instances
  - Cached injectables
  - Error handling
  - Validation

- **test_optional_lazy.py** (15 tests): Comprehensive tests for `OPTIONAL_LAZY` evaluation strategy
  - Lazy vs optional lazy comparison
  - Registered dependencies
  - Mixed registered/unregistered dependencies
  - Custom containers
  - Manual overrides
  - `@wired` decorator integration
  - All unregistered dependencies
  - Default values
  - `__post_init__` behavior
  - Partial registration
  - Validation
  - Container isolation
  - Dependency caching
  - Class inheritance
  - Error handling in registered dependencies

- **test_field_lazy.py** (21 tests): Comprehensive tests for field-level lazy annotations
  - Lazy fields in eager class
  - Multiple lazy fields
  - Field-level lazy with class-level `LAZY`
  - `OptionalLazy` marker
  - Manual overrides
  - `@wired` decorator integration
  - Default values
  - Dependency caching
  - Custom containers
  - Class inheritance
  - All eager except one field
  - Validation
  - `__post_init__` behavior
  - Error handling
  - Multiple instances
  - Mixing `Lazy` and `OptionalLazy` markers

### Documentation

- Added comprehensive docstrings to marker classes explaining usage patterns
- Included code examples in marker class documentation

## Notes

### Performance Benefits

Lazy evaluation provides several performance benefits:
- **Deferred initialization**: Expensive dependencies only created when needed
- **Conditional usage**: Dependencies that may not be used in all code paths aren't created unnecessarily
- **Startup time**: Reduced application startup time by deferring non-critical dependency creation
- **Memory efficiency**: Only allocate resources for dependencies that are actually accessed

### Design Decisions

1. **Property-based implementation**: Lazy fields use Python properties for transparent access while maintaining lazy semantics
2. **Singleton markers**: Type-safe markers that can be used with IDE autocomplete and static type checking
3. **Caching**: Lazy dependencies cache their resolved value to ensure single instantiation per class instance
4. **Optional lazy**: Separate `OPTIONAL_LAZY` strategy and `OptionalLazy` marker to distinguish between required and optional dependencies

### Migration Guide

For existing code, no changes are required. The default behavior remains `EAGER` evaluation. To adopt lazy evaluation:

1. **Class-level lazy**: Add `evaluation_strategy` parameter to `@injected` or `@wired`:
   ```python
   @injected(evaluation_strategy=EvaluationStrategy.LAZY)
   class MyClass:
       ...
   ```

2. **Field-level lazy**: Use `Annotated` with `Lazy` or `OptionalLazy` markers:
   ```python
   from typing import Annotated
   from dependify import injected, Lazy, OptionalLazy

   @injected
   class MyClass:
       expensive: Annotated[ExpensiveService, Lazy]
       optional: Annotated[OptionalService, OptionalLazy]
   ```

[Unreleased]: https://github.com/yourusername/dependify/compare/v0.1.0...HEAD
