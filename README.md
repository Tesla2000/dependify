<div style="display: flex; justify-content: center">
    <img src="https://github.com/KennethUlloa/dependify/raw/main/images/dependify.svg" width="80%">
</div>

# Dependify
Dependify is a library that aims to reduce the effort that comes with the manual handling of dependency injection by automating as much as it can. 

### The problem
Imagine that you have some class that requires some functions provided by other classes. If you have to instantiate manually all the dependencies in multiple places, it might get messy really quick. 
```python
# Your classes with good coding practices ;)
class A:
    def __init__(self):
        pass

class B:
    def __init__(self, a: A):
        self.a = A

class C:
    def __init__(self, b: B):
        self.b = B

# But then, the hell...
def use_a():
    a = A()
    # do something with A

def use_b():
    a = A()
    b = B(a)
    # do something with B

def use_c():
    a = A()
    b = B(a)
    c = C(b)
    # do something with C
```
When you want to decouple the classes from direct references (like dependency instantiation inside of a constructor) you use arguments to separate the use from the creation (dependency injection principle).

This make your code easier to scale, grow and its a strong step in the direction of using **SOLID** principles in your code.

The problems comes when each dependency has its own dependencies.

You can instantiate each of them by yourself as seen in the example. But your code will become more complex and so the classes. To use an specific dependency you have to handle its dependencies and this will force you to remember every dependency's dependencies.

Your first approach might be to define some module that contains all dependency creation logic.
```python
from a_module import A, A1
from b_module import B, B1
from c_module import C, C1
from d_module import D, D1


def create_a():
    return A()

def create_a1():
    return A1()

def create_b():
    return B(create_a())

def create_b1():
    return B1(create_a1())

def create_c():
    return C(create_b())

def create_d():
    return D(create_a(), create_b1())

# And so on...
```
Then you'll have any sort of combinations of dependencies that will be hard to track or modify. 

Dependify offers to take this bullet for you by automatically instantiating and wiring up dependencies so you can focus on creating value with your solution.

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
All dependencies are stored globally, meaning they will be accessible through all the code as long the registration happends before usage.

You can register a dependency for a type using the same type or passing a different type/callable using the `patch` keyword argument.
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

You're not limited to classes to define dependencies, callables also can be registered as dependencies for a type.
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
In the backstage Dependify uses a global `Container` object to hold all dependencies. But you can also use your own. The `inject` decorator has an optional keyword called `container` so you can use localized injection with different dependencies for the same type. It means you can have localized dependencies that doesn't crash with global dependencies.
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

#### Flags
Either in `Dependency` constructor or in `register` method can specify the following flags to modify the injection behaviour for a dependency.
- `cache` determines whether to store the result of the first call of the dependency. Defaults to `False`.
- `autowire` determines whether to autowire the arguments declared in the dependency. This feature allows you to decide how to initialize internal dependencies if set to `False`. Defaults to `True`.
```python
# Cached instance example
from dependify import register, inject

class HelloPrinter:
    def __init__(self):
        self.last = None
    
    def say_hello(self, name: str):
        print("Before I said hi to", self.last)
        print(f"Hello {name}")
        self.last = name

# register your class as a cached dependency 
register(HelloPrinter, cache=True)

# inject the dependency in the place you need (has to be a callable)
@inject
def hello_dev(printer: HelloPrinter):
    printer.say_hello("Developer")

# reuse the object
@inject
def hello_po(printer: HelloPrinter):
    printer.say_hello("Product Owner")
 
hello_dev()
hello_po()
```
Since we are sharing the `HelloPrinter` instance between functions, any change made to it will be accessible by the next function and so on. In this example we are storing the last name that was passed to the `say_hello` method.

The output  would look similar to this
```
Before I said hi to None
Hello Developer
Before I said hi to Developer
Hello Product Owner
```
Even though the dependency was instantiated out of scene, we are using the same instace throughout the program. 

This could be useful when we have a dependency that must store its state like a database connection or some api client whose instantiation is resource-costly.

#### The catch
Sadly, anything in life is perfect. Dependify is not the exception. 

If you want to use the decorators you are tied to use injection in callables only if you want to keep your domain clean from any dependency.
```python
from dependify import injectable, inject

@injectable
class A:
    pass

@injectable
class B:
    def __init__(self, b: B):
        self.b = B

# Bad use
def main():
    b = B() # this will break since it is specting an instance of A

# Working code
@inject
def main(b: B):
    # do something with B
``` 
If you don't need (or want) to use decorators, you can use the function-based way.
```python
from dependify import register, resolve

class A:
    pass

class B:
    def __init__(self, b: B):
        self.b = B

register(A)
register(B)

# This will work since you are calling the resolve 
# logic insted of direct instantiation, so 
# dependify will handle all registered 
# dependencies
def main():
    b = resolve(B)
    # Do something with B
```
The good news are that you can mix both ways of using the registration/injection logic. 
```python
from dependify import injectable, inject, register, resolve

# Register A with decorator
@injectable
class A:
    pass

class B:
    def __init__(self, b: B):
        self.b = B

# Register B with function
register(B)


# Inject B with decorator
@inject
def main(b: B):
    # Do something with B

# Inject A with function
def main2():
    a = resolve(A)
```
If your classes can be decorated then the usage of a dependant class becomes much easier.
```python
from dependify import injectable, inject

@injectable
class A:
    pass

@injectable
class B:
    pass


class C:
    @inject
    def __init__(self, a: A, b: B):
        pass

# This will work since the constructor is decorated and 
# its dependencies are automatically resolved.
c = C() 
```