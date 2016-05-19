import eventlet
from nameko.standalone.rpc import ClusterRpcProxy

from egor.service.load.loader import RpcProxyLazyLoader


class GitLoader(RpcProxyLazyLoader):
    def __init__(self, base_path, cluster, *initial):
        self.base_path = base_path
        self.cluster = cluster
        super().__init__(*initial)

    def load(self, name, uri=None):
        super().load(name)
        if uri is None:
            uri = '/'.join((self.base_path, name + '.git'))
        return eventlet.spawn(self.install_service, name, uri)

    def install_service(self, name, uri):
        with ClusterRpcProxy({
            'AMQP_URI': self.cluster
        }) as proxy:
            proxy.servicehost.prep(name, uri)
            self.resolve(name)
