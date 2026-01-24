from unittest import TestCase

from dependify import DependencyInjectionContainer
from dependify import Inject


class TestInject(TestCase):

    def test_inject_with_container(self):
        """
        Test if the `Inject` decorator can be used with a custom container.
        """

        class A:
            pass

        container = DependencyInjectionContainer()
        container.register(A)

        inject = Inject(container)

        @inject
        def test(a: A):
            self.assertIsInstance(a, A)

        test()
