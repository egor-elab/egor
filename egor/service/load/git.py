import os

import eventlet
from nameko.standalone.rpc import ClusterRpcProxy

from egor.service.load.loader import RpcProxyLazyLoader


class GitLoader(RpcProxyLazyLoader):
    def __init__(self, base_path, cluster, *initial):
        self.base_path = base_path
        self.cluster = cluster
        super().__init__(*initial)

    def load(self, name):
        super().load(name)
        eventlet.spawn(self.install_service, name)

    def install_service(self, name):
        with ClusterRpcProxy({
            'AMQP_URI': self.cluster
        }) as proxy:
            proxy.servicehost.prep(
                name,
                os.path.join(self.base_path, name, '.git')
            )
            self.resolve(name)
            self._proxies.append(name)
