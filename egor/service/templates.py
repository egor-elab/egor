from nameko.rpc import rpc


class BaseService:
    @rpc
    def up(self):
        pass

    @rpc
    def down(self):
        pass
