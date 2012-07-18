import logging
import unittest

import newrelic.api.settings
import newrelic.api.application
import newrelic.api.transaction
import newrelic.api.web_transaction

_logger = logging.getLogger('newrelic')

settings = newrelic.api.settings.settings()

settings.host = 'staging-collector.newrelic.com'
settings.license_key = '84325f47e9dec80613e262be4236088a9983d501'

settings.app_name = 'Python Unit Tests'

settings.log_file = '%s.log' % __file__
settings.log_level = logging.DEBUG

settings.transaction_tracer.transaction_threshold = 0
settings.transaction_tracer.stack_trace_threshold = 0

settings.shutdown_timeout = 10.0

settings.debug.log_data_collector_calls = True
settings.debug.log_data_collector_payloads = True

_application = newrelic.api.application.application_instance("UnitTests")
_application.activate(timeout=10.0)

def _wsgiapp_function(self, *args):
    transaction = newrelic.api.transaction.current_transaction()
    assert transaction != None
_wsgiapp_function = newrelic.api.web_transaction.WSGIApplicationWrapper(
        _wsgiapp_function, _application)

def _wsgiapp_function_error(self, *args):
    raise RuntimeError("_wsgiapp_function_error")
_wsgiapp_function_error = newrelic.api.web_transaction.WSGIApplicationWrapper(
        _wsgiapp_function_error, _application)

class _wsgiapp_class:
    def __init__(self, *args):
        pass
    def __call__(self):
        transaction = newrelic.api.transaction.current_transaction()
        assert transaction != None
_wsgiapp_class = newrelic.api.web_transaction.WSGIApplicationWrapper(
        _wsgiapp_class, _application)

@newrelic.api.web_transaction.wsgi_application("UnitTests")
def _wsgiapp_function_decorator(self, *args):
    transaction = newrelic.api.transaction.current_transaction()
    assert transaction != None

@newrelic.api.web_transaction.wsgi_application()
def _wsgiapp_function_decorator_default(self, *args):
    transaction = newrelic.api.transaction.current_transaction()
    assert transaction != None

@newrelic.api.web_transaction.wsgi_application("UnitTests")
class _wsgiapp_class_decorator:
    def __init__(self, *args):
        pass
    def __call__(self):
        transaction = newrelic.api.web_transaction.current_transaction()
        assert transaction != None

class WSGIApplicationTests(unittest.TestCase):

    def setUp(self):
        _logger.debug('STARTING - %s' % self._testMethodName)

    def tearDown(self):
        _logger.debug('STOPPING - %s' % self._testMethodName)

    def test_wsgiapp_function(self):
        environ = { "REQUEST_URI": "/wsgiapp_function" }
        _wsgiapp_function(environ, None).close()

    def test_wsgiapp_function_error(self):
        environ = { "REQUEST_URI": "/wsgiapp_function_error" }
        try:
            _wsgiapp_function_error(environ, None)
        except RuntimeError:
            pass

    def _wsgiapp_method(self, *args):
        transaction = newrelic.api.transaction.current_transaction()
        self.assertNotEqual(transaction, None)
    _wsgiapp_method = newrelic.api.web_transaction.WSGIApplicationWrapper(
            _wsgiapp_method, _application)

    def test_wsgiapp_method(self):
        environ = { "REQUEST_URI": "/wsgiapp_method" }
        self._wsgiapp_method(environ, None).close()

    def test_wsgiapp_class(self):
        environ = { "REQUEST_URI": "/wsgiapp_class" }
        _wsgiapp_class(environ, None).close()

    def test_wsgiapp_function_decorator(self):
        environ = { "REQUEST_URI": "/wsgiapp_function_decorator" }
        _wsgiapp_function_decorator(environ, None).close()

    def test_wsgiapp_function_decorator_default(self):
        environ = { "REQUEST_URI": "/wsgiapp_function_decorator_default" }
        _wsgiapp_function_decorator_default(environ, None).close()

    @newrelic.api.web_transaction.wsgi_application("UnitTests")
    def _wsgiapp_method_decorator(self, *args):
        transaction = newrelic.api.transaction.current_transaction()
        self.assertNotEqual(transaction, None)

    def test_wsgiapp_method_decorator(self):
        environ = { "REQUEST_URI": "/wsgiapp_method_decorator" }
        self._wsgiapp_method_decorator(environ, None).close()

    def test_wsgiapp_class_decorator(self):
        environ = { "REQUEST_URI": "/wsgiapp_class_decorator" }
        _wsgiapp_class_decorator(environ, None).close()

if __name__ == '__main__':
    unittest.main()
