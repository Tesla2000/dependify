<div style="display: flex; justify-content: center">
    <img src="./images/dependify.svg" width="80%">
</div>

# Dependify
Dependency injection library


## Description
Declarative library for handling dependency injection with minimal configuration.

## Usage
#### Out of the box usage
```python
from dependify import injectable, inject

# Register a class as a dependency with 'injectable' decorator
@injectable
class SomeDependency:
    def __init__(self):
        pass

class SomeDependantClass:
    # Decorate a callable to inject the dependencies
    @inject
    def __init__(self, some_dependency: SomeDependency):
        self.some_dependency = some_dependency

# Instantiation
# No need to pass arguments since they are being handled by dependify
dependant = SomeDependantClass()
```
All dependencies are stored at module level, meaning they will be accessible through all the code you need as long the registration happends before usage.

You can register a dependency for a type using the same type or passing a different type/callable.
```python
# Register an interface for injection
# interface definition: abc or protocols
from dependify import injectable, inject


class IService(ABC):
    @abstractmethod
    def method(self):
        pass


# Register ServiceImpl to be injected instead of IService
@injectable(patch=IService)
class ServiceImpl(IService):
    # Class implementation
    def method(self):
        # Some implementation


# usage of service
@inject
def do_something_with_service(service: IService):
    service.method()
```

You're not limited to classes to define dependencies, callables also can be registered as dependencies.
```python
from dependify import injectable, inject

# Some classes dependencies might need a complex setting up process 
# that can't be put as a dependency due some factors 
# (standard types dependencies for example).
class DatabaseHandler:
    # The following init method needs a string but
    # it will be a non-sense to register 'str' type as a
    # dependency
    def __init__(self, str_con: str):
        ...
    
    def get_clients(self) -> list:
        ...


# Here we define a pre initialization process and
# mark the dependency as 'cached' so it will be 
# instantiated once and it will save the object to
# future calls. Same result could be achieved with
# @cached. But the goal of the decorator is to reduce
# redundant decorators related to usage.
@injectable(patch=DatabaseHandler, cached=True)
def create_db_handler():
    import os
    return DatabaseHandler(os.getenv('DB_CONN_STR'))

@inject
def get_clients_from_db(db_handler: DatabaseHandler):
    clients = db_handler.get_clients()
    # Do something else with result
```
In the previous example you were able to use a predefined process to create an specific dependency. Notice that you must use the `patch` keyword when decorating functions since all functions have the same type always.
##### External register
If for some reason you don't want to anotate your classes (you are using a clean architecture for example), then you can register your classes and callables using the `register` function.

```python
# use case file
from core.users.repository import IUserRepository


class ListUsersUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository
    
    def execute(self) -> list[User]:
        return self.repository.find_all()

# config file
from dependify import register
from core.users.usecases import ListUsersUseCase

register(ListUsersUseCase)

# controller file (flask in this example)
import config # You make sure that registration happends
from flask import Flask
from dependify import inject
from core.users.usecases import ListUsersUseCase


app = Flask(__name__)


@app.get('/users')
@inject
def get_all_users(
    use_case: ListUsersUseCase
):
    users = use_case.execute()
    # Serialization to json
    return serialized_users

```

#### Localized dependencies
In the backstage Dependify uses a `Container` object to hold all dependencies. But you can also use your own. The `inject` decorator has an optional keyword called `container` so you can use localized injection with different dependencies for same types. It means you can have localized dependencies that doesn't crash with global dependencies.
```python
from dependify import Container, inject, register

class SomeClass:
    pass

my_container = Container()
my_container.register(SomeClass)

# If we declare a function and decorate it with 'inject' 
# it won't work and instead raise an exception. 
# This is because the global 'Container' it's not aware 
# of the SomeClass type.
@inject
def use_some_class(some_class: SomeClass):
    pass

# Now if we use the 'container' keyword, it won't fail
# and continue the normal flow.
@inject(container=my_container)
def use_some_class(some_class: SomeClass):
    pass
```

Another way of using your own container is setting it as the global container.
```python
from dependify import Container, set_container

class SomeClass:
    pass

my_container = Container()
my_container.register(SomeClass)


set_container(my_container)

@inject
def use_some_class(some_class: SomeClass):
    pass
```
