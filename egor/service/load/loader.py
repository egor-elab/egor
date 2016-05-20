from nameko.extensions import DependencyProvider
from nameko.rpc import (
    MethodProxy,
    ServiceProxy,
    ReplyListener,
)
from nameko.standalone.rpc import ClusterRpcProxy

from eventlet.event import Event


class DependencyNotLoadedError(Exception):
    pass


class LazyMethodProxy(MethodProxy):
    def __init__(self, loaded, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded = loaded

    def __call__(self, *args, **kwargs):
        print(self._loaded)
#        import pdb; pdb.set_trace()
        if not self._loaded.ready():
            raise DependencyNotLoadedError
        return super().__call__(*args, **kwargs)

    def call_blocking(self, *args, **kwargs):
        self._loaded.wait()
        return super().__call__(*args, **kwargs)


class LazyServiceProxy(ServiceProxy):
    def __init__(self, loaded, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded = loaded

    def __getattr__(self, name):
        return LazyMethodProxy(
            self._loaded,
            self.worker_ctx,
            self.service_name,
            name,
            self.reply_listener
        )

    # def load_complete(self):
    #     self._loaded.send()


class LazyRpcProxy(DependencyProvider):
    rpc_reply_listener = ReplyListener()

    def __init__(self, target_service, loaded):
        self.target_service = target_service
        self._loaded = loaded

    def get_dependency(self, worker_ctx):
        return LazyServiceProxy(
            self._loaded,
            worker_ctx,
            self.target_service,
            self.rpc_reply_listener
        )


class RpcProxyLazyLoader:
    def __init__(self, *initial):
        self._proxies_pending = {}
        self._proxies_active = set()
        for name in initial:
            self.load(name)

    def load(self, name):
        self._proxies_pending[name] = Event()
        print('created event {}'.format(self._proxies_pending[name]))
        return self._proxies_pending[name]

    def resolve(self, name):
        print('resolving event {}'.format(self._proxies_pending[name]))
        self._proxies_pending[name].send()
        self._proxies_active.add(name)

    def get(self, name):
        return LazyRpcProxy(name, self._proxies_pending[name])

    def wait(self, key=None):
        if key is not None:
            self._proxies_pending[key].wait()
        else:
            for key, event in self._proxies_pending.items():
                event.wait()

    def list_pending(self):
        return set(self._proxies_pending.keys()) - self._proxies_active

    def list_active(self):
        return self._proxies_active


class InjectableLazyLoader(DependencyProvider):
    def __init__(self, loader):
        self.loader = loader

    def get_dependency(self, worker_ctx):
        return {
            name: self.loader.get(name).get_dependency(worker_ctx)
            for name in self.loader._proxies_active
        }
