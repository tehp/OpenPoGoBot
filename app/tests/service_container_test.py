import unittest

import pytest
from mock import Mock

from app import ServiceContainer
from app.exceptions import ServiceNotFoundException, ContainerAlreadyBootedException


class PluginsTest(unittest.TestCase):
    @staticmethod
    def test_register_singleton():
        service_container = ServiceContainer()

        service = Mock()
        service_container.register_singleton('mock_service', service)
        service_container.boot()

        assert service_container.has('mock_service') is True
        assert service_container.get('mock_service') is service

    @staticmethod
    def test_register_decorator():
        service_container = ServiceContainer()

        @service_container.register('test_service')
        class TestService(object):
            pass

        service_container.boot()

        assert service_container.has('test_service') is True
        assert isinstance(service_container.get('test_service'), TestService) is True

    @staticmethod
    def test_get_service_unknown():
        service_container = ServiceContainer()
        service_container.boot()

        with pytest.raises(ServiceNotFoundException):
            service_container.get('test_service')

    @staticmethod
    def test_register_decorator_args():
        service_container = ServiceContainer()

        another_service = Mock()
        service_container.register_singleton('another_service', another_service)

        param_service = Mock()
        service_container.register_singleton('param_service', param_service)

        service_container.set_parameter('test_param', 'hello')
        service_container.set_parameter('service_param', 'param_service')

        @service_container.register('test_service', ['@another_service', '%test_param%', '%service_param%', 'static'])
        class TestService(object):
            def __init__(self, ts_another_service, ts_test_param, ts_param_service, ts_static_val):
                self.another_service = ts_another_service
                self.test_param = ts_test_param
                self.param_service = ts_param_service
                self.static_val = ts_static_val

        service_container.boot()

        test_service = service_container.get('test_service')
        assert service_container.has('test_service') is True
        assert isinstance(test_service, TestService) is True

        assert test_service.another_service is another_service
        assert test_service.test_param is 'hello'
        assert test_service.param_service is param_service
        assert test_service.static_val is 'static'

    @staticmethod
    def test_register_decorator_kwargs():
        service_container = ServiceContainer()

        another_service = Mock()
        service_container.register_singleton('another_service', another_service)

        param_service = Mock()
        service_container.register_singleton('param_service', param_service)

        service_container.set_parameter('test_param', 'hello')
        service_container.set_parameter('service_param', 'param_service')

        @service_container.register('test_service', keywordsargs={'ts_another_service': '@another_service', 'ts_test_param': '%test_param%', 'ts_param_service': '%service_param%', 'ts_static_val': 'static'})
        class TestService(object):
            def __init__(self, ts_another_service=None, ts_test_param=None, ts_param_service=None, ts_static_val=None):
                self.another_service = ts_another_service
                self.test_param = ts_test_param
                self.param_service = ts_param_service
                self.static_val = ts_static_val

        service_container.boot()

        test_service = service_container.get('test_service')
        assert service_container.has('test_service') is True
        assert isinstance(test_service, TestService) is True

        assert test_service.another_service is another_service
        assert test_service.test_param is 'hello'
        assert test_service.param_service is param_service
        assert test_service.static_val is 'static'

    @staticmethod
    def test_register_tags():
        service_container = ServiceContainer()

        another_service = Mock()
        service_container.register_singleton('another_service', another_service, tags=['tag_one', 'tag_two', 'tag_three'])

        @service_container.register('test_service', tags=['tag_one', 'tag_two'])
        # pylint: disable=unused-variable
        class TestService(object):
            def __init__(self, ts_another_service=None, ts_test_param=None, ts_param_service=None, ts_static_val=None):
                self.another_service = ts_another_service
                self.test_param = ts_test_param
                self.param_service = ts_param_service
                self.static_val = ts_static_val

        service_container.boot()

        tag_one_services = service_container.get_by_tag('tag_one')
        tag_two_services = service_container.get_by_tag('tag_two')
        tag_three_services = service_container.get_by_tag('tag_three')
        tag_four_services = service_container.get_by_tag('tag_four')

        assert len(tag_one_services) is 2
        assert len(tag_two_services) is 2
        assert len(tag_three_services) is 1
        assert len(tag_four_services) is 0

    @staticmethod
    def test_compiler_pass():
        service_container = ServiceContainer()

        @service_container.register_compiler_pass()
        # pylint: disable=unused-variable
        def compiler_pass(sc):
            sc.set_parameter('compiler_set', 'test')

        service_container.boot()

        assert service_container.get_parameter('compiler_set') is 'test'

    @staticmethod
    def test_compiler_pass_already_booted():
        service_container = ServiceContainer()
        service_container.boot()

        with pytest.raises(ContainerAlreadyBootedException):
            @service_container.register_compiler_pass()
            # pylint: disable=unused-variable
            def compiler_pass(sc):
                sc.set_parameter('compiler_set', 'test')

    @staticmethod
    def test_boot_already_booted():
        service_container = ServiceContainer()
        service_container.boot()

        with pytest.raises(ContainerAlreadyBootedException):
            service_container.boot()
