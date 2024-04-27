from container import Container
from decorators import register, inject, injectable



class A:

    def __init__(self):
        print("A created")

@injectable
class B:
    
    def __init__(self):
        print("AnotherInjectedClass created")

@injectable
class C:
    
    def __init__(self, an_injected_class: A):
        print("ThirdInjectedClass created")
        print(" ",an_injected_class, "injected")

@injectable(patch=A, cached=True)
def creating_a():
    print("Creating A")
    return A()


@inject
def main(an_injected_class: A, another_injected_class: B, third_injected_class: C):
    print("Main function")
    print(" ",an_injected_class, "injected")
    print(" ",another_injected_class, "injected")
    print(" ",third_injected_class, "injected")

main()