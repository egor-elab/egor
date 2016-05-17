import os

import eventlet
from nameko.standalone.rpc import ClusterRpcProxy

from egor.service.load.loader import RpcProxyLazyLoader


class GitLoader(RpcProxyLazyLoader):
    def __init__(self, base_path, cluster, *initial):
        self.base_path = base_path
        self.cluster = cluster
        super().__init__(*initial)

    def load(self, name, bare=True):
        super().load(name)
        eventlet.spawn(self.install_service, name, bare)

    def install_service(self, name, bare):
        with ClusterRpcProxy({
            'AMQP_URI': self.cluster
        }) as proxy:
            if bare:
                reponame = name + '.git'
            else:
                reponame = os.path.join(name, '.git')
            proxy.servicehost.prep(
                name,
                os.path.join(self.base_path, reponame)
            )
            self.resolve(name)
            self._proxies.append(name)
