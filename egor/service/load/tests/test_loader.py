import pytest
from nameko.rpc import rpc
from nameko.testing.utils import get_container
from nameko.testing.services import entrypoint_hook

from egor.service.load.loader import (
    RpcProxyLazyLoader,
    DependencyNotLoadedError,
)


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


loader = RpcProxyLazyLoader('dependency1', 'dependency2')


class ServiceWithLazyLoadedDependencies:
    name = 'lazydeps'
    dependency1 = loader.get('dependency1')
    dependency2 = loader.get('dependency2')

    @rpc
    def resolve(self, which):
        loader.resolve(which)

    @rpc
    def load(self, which):
        loader.load(which)

    @rpc
    def call(self, which):
        return getattr(self, which).hello()


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


def test_loader(runner):
    container = get_container(runner, ServiceWithLazyLoadedDependencies)

    with entrypoint_hook(container, 'resolve') as entrypoint:
        entrypoint('dependency1')
    with entrypoint_hook(container, 'call') as entrypoint:
        assert entrypoint('dependency1') == 'world'
        with pytest.raises(DependencyNotLoadedError):
            entrypoint('dependency2')

    with entrypoint_hook(container, 'resolve') as entrypoint:
        entrypoint('dependency2')
    with entrypoint_hook(container, 'call') as entrypoint:
        assert entrypoint('dependency2') == 'there'

    container = get_container(runner, NeighborService)
    with entrypoint_hook(container, 'call') as entrypoint:
        assert entrypoint() == 'world'

    loader.wait()
    assert all(e.ready() for e in loader._proxies_pending.values())
    assert not len(loader.list_pending())
    assert len(loader.list_active())
