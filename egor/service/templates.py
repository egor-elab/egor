import os
import yaml

from nameko.rpc import rpc


def configure(base, files):
    config = {}
    for file in files:
        with open(os.path.join(
            base,
            'config',
            file + '.yaml'
        )) as f:
            config[file] = yaml.load(f)
    return config


class BaseService:
    @rpc
    def up(self):
        pass

    @rpc
    def down(self):
        pass
