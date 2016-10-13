import psycopg2
import pytest

from testing_support.fixtures import (validate_transaction_metrics,
    validate_database_trace_inputs, override_application_settings)
from utils import instance_hostname, DB_SETTINGS, PSYCOPG2_VERSION

from newrelic.agent import background_task


# Settings

_enable_instance_settings = {
    'datastore_tracer.instance_reporting.enabled': True,
}
_disable_instance_settings = {
    'datastore_tracer.instance_reporting.enabled': False,
}

# Metrics

_base_scoped_metrics = (
        ('Function/psycopg2:connect', 1),
        ('Datastore/operation/Postgres/rollback', 1)
)

_base_rollup_metrics = (
        ('Datastore/all', 2),
        ('Datastore/allOther', 2),
        ('Datastore/Postgres/all', 2),
        ('Datastore/Postgres/allOther', 2),
        ('Datastore/operation/Postgres/rollback', 1)
)

_enable_scoped_metrics = list(_base_scoped_metrics)
_enable_rollup_metrics = list(_base_rollup_metrics)

_disable_scoped_metrics = list(_base_scoped_metrics)
_disable_rollup_metrics = list(_base_rollup_metrics)

_host = instance_hostname(DB_SETTINGS['host'])
_port = DB_SETTINGS['port']

_enable_scoped_metrics.append(
        ('Datastore/instance/Postgres/%s/%s' % (_host, _port), 1)
)
_enable_rollup_metrics.append(
        ('Datastore/instance/Postgres/%s/%s' % (_host, _port), 1)
)

# Query

def _exercise_db():
    try:
        with psycopg2.connect(
                database=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
                password=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
                port=DB_SETTINGS['port']):

            raise RuntimeError('error')
    except RuntimeError:
        pass

# Tests

@pytest.mark.skipif(PSYCOPG2_VERSION < (2, 5),
        reason='Context manager support introduced in psycopg2 version 2.5')
@override_application_settings(_enable_instance_settings)
@validate_transaction_metrics(
        'test_rollback:test_rollback_on_exception_enable_instance',
        scoped_metrics=_enable_scoped_metrics,
        rollup_metrics=_enable_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_rollback_on_exception_enable_instance():
    _exercise_db()


@pytest.mark.skipif(PSYCOPG2_VERSION < (2, 5),
        reason='Context manager support introduced in psycopg2 version 2.5')
@override_application_settings(_disable_instance_settings)
@validate_transaction_metrics(
        'test_rollback:test_rollback_on_exception_disable_instance',
        scoped_metrics=_disable_scoped_metrics,
        rollup_metrics=_disable_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_rollback_on_exception_disable_instance():
    _exercise_db()
