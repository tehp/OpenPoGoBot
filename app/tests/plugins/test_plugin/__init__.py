from app.tests import test_kernel


@test_kernel.container.register('test_plugin', tags=['plugin'])
class TestPlugin(object):
    pass
