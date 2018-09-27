import pytest
import requests

from testing_support.fixtures import override_application_settings
from testing_support.validators.validate_span_events import (
        validate_span_events)
from testing_support.mock_external_http_server import MockExternalHTTPServer
from newrelic.api.background_task import background_task
from newrelic.api.transaction import current_transaction


@pytest.fixture(scope='module', autouse=True)
def server():
    with MockExternalHTTPServer():
        yield


@pytest.mark.parametrize('path', ('', '/foo', '/' + 'a' * 256))
def test_span_events(path):
    _settings = {
        'distributed_tracing.enabled': True,
        'span_events.enabled': True,
    }

    uri = 'http://localhost:8989'
    if path:
        uri += path

    expected_uri = uri[:255]

    exact_intrinsics = {
        'name': 'External/localhost:8989/requests/',
        'type': 'Span',
        'sampled': True,
        'priority': 0.5,

        'category': 'http',
        'span.kind': 'client',
        'http.url': expected_uri,
        'component': 'requests',
    }
    expected_intrinsics = ('timestamp', 'duration', 'transactionId')

    @override_application_settings(_settings)
    @validate_span_events(
            count=1,
            exact_intrinsics=exact_intrinsics,
            expected_intrinsics=expected_intrinsics)
    @background_task(name='test_span_events')
    def _test():
        txn = current_transaction()
        txn._priority = 0.5
        txn._sampled = True

        response = requests.get(uri)
        response.raise_for_status()

    _test()
