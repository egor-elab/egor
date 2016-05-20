import logging
import pytest
import sys

from nameko.rpc import rpc
from nameko.testing.utils import get_container
from nameko.testing.services import entrypoint_hook

from egor.service.load.loader import (
    RpcProxyLazyLoader,
    DependencyNotLoadedError,
    InjectableLazyLoader,
)


logging.basicConfig(level=logging.WARNING, stream=sys.stdout)


class DependencyOne:
    name = 'dependency1'

    @rpc
    def hello(self):
        return 'world'


class DependencyTwo:
    name = 'dependency2'

    @rpc
    def hello(self):
        return 'there'


loader = RpcProxyLazyLoader('dependency1')


class ServiceWithLazyLoadedDependencies:
    name = 'lazydeps'
    dependency1 = loader.get('dependency1')
    loaded_deps = InjectableLazyLoader(loader)

    @rpc
    def load(self, which):
        loader.load(which)

    @rpc
    def resolve(self, which):
        loader.resolve(which)

    @rpc
    def call_1(self):
        return self.dependency1.hello()

    @rpc
    def call(self, which):
        return self.loaded_deps[which].hello()

    @rpc
    def wait(self):
        loader.wait()


class NeighborService:
    name = 'neighbor'
    dependency = loader.get('dependency1')

    @rpc
    def call(self):
        return self.dependency.hello()


@pytest.yield_fixture
def runner(rabbit_config, runner_factory):
    runner = runner_factory(
        rabbit_config,
        ServiceWithLazyLoadedDependencies, NeighborService,
        DependencyOne, DependencyTwo
    )
    runner.start()
    yield runner


def with_helper(ct, ep, *args):
    with entrypoint_hook(ct, ep) as entrypoint:
        return entrypoint(*args)


def test_loader(runner):
#    caplog.setLevel(logging.WARNING)
    container = get_container(runner, ServiceWithLazyLoadedDependencies)

    with entrypoint_hook(container, 'call_1') as entrypoint:
        with pytest.raises(DependencyNotLoadedError):
            entrypoint()

    with_helper(container, 'resolve', 'dependency1')
    assert with_helper(container, 'call_1') == 'world'

    with_helper(container, 'load', 'dependency2')
    with_helper(container, 'resolve', 'dependency2')
    with_helper(container, 'wait')
    # assert with_helper(container, 'call', 'dependency2') == 'there'

    # container = get_container(runner, NeighborService)
    # assert with_helper(container, 'call') == 'world'

    assert all(e.ready() for e in loader._proxies_pending.values())
    assert not len(loader.list_pending())
    assert len(loader.list_active())
