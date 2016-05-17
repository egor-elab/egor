import os

import pytest
from nameko.standalone.rpc import ClusterRpcProxy

from egor.service.load.git import GitLoader


LOCALROOT = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def file_config():
    return {
        'repo_root': os.path.join(LOCALROOT, '../../../../..'),
    }


def test_install(file_config):
    loader = GitLoader(
        file_config['repo_root'],
        'amqp://guest:guest@localhost:5672'
    )
    loader.load('blank', bare=False)
    assert len(loader.list_pending())
    loader.wait()

    config = {
        'AMQP_URI': 'amqp://guest:guest@localhost:5672'
    }
    with ClusterRpcProxy(config) as rpc:
        assert rpc.servicehost.find('blank')
        assert os.path.isdir(
            os.path.join(
                rpc.servicehost.base_path(),
                'blank',
                '.git'
            )
        )
