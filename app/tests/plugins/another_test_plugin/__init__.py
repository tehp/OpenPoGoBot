from app.tests import test_kernel


@test_kernel.container.register('another_test_plugin', tags=['plugin'])
class AnotherTestPlugin(object):
    pass
