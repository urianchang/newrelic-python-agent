import json
import re

import psycopg2
import psycopg2.extensions
import psycopg2.extras
import pytest

from testing_support.fixtures import (validate_transaction_metrics,
    validate_database_trace_inputs, validate_transaction_errors)

from testing_support.settings import postgresql_settings

from newrelic.agent import background_task

DB_SETTINGS = postgresql_settings()

def _to_int(version_str):
    m = re.match(r'\d+', version_str)
    return int(m.group(0)) if m else 0

def version2tuple(version_str):
    """Convert version, even if it contains non-numeric chars.

    >>> version2tuple('9.4rc1.1')
    (9, 4)

    """

    parts = version_str.split('.')[:2]
    return tuple(map(_to_int, parts))

def postgresql_version():
    with psycopg2.connect(
            database=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
            password=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']) as connection:

        cursor = connection.cursor()
        cursor.execute("""SELECT setting from pg_settings where name=%s""",
                ('server_version',))

        return cursor.fetchone()

POSTGRESQL_VERSION = version2tuple(postgresql_version()[0])

_test_execute_via_cursor_scoped_metrics = [
        ('Function/psycopg2:connect', 1),
        ('Function/psycopg2.extensions:connection.__enter__', 1),
        ('Function/psycopg2.extensions:connection.__exit__', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/select', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/insert', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/update', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/delete', 1),
        ('Datastore/statement/Postgres/now/call', 1),
        ('Datastore/statement/Postgres/pg_sleep/call', 1),
        ('Datastore/operation/Postgres/drop', 1),
        ('Datastore/operation/Postgres/create', 1),
        ('Datastore/operation/Postgres/commit', 3),
        ('Datastore/operation/Postgres/rollback', 1)]

_test_execute_via_cursor_rollup_metrics = [
        ('Datastore/all', 13),
        ('Datastore/allOther', 13),
        ('Datastore/Postgres/all', 13),
        ('Datastore/Postgres/allOther', 13),
        ('Datastore/operation/Postgres/select', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/select', 1),
        ('Datastore/operation/Postgres/insert', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/insert', 1),
        ('Datastore/operation/Postgres/update', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/update', 1),
        ('Datastore/operation/Postgres/delete', 1),
        ('Datastore/statement/Postgres/datastore_psycopg2/delete', 1),
        ('Datastore/operation/Postgres/drop', 1),
        ('Datastore/operation/Postgres/create', 1),
        ('Datastore/statement/Postgres/now/call', 1),
        ('Datastore/statement/Postgres/pg_sleep/call', 1),
        ('Datastore/operation/Postgres/call', 2),
        ('Datastore/operation/Postgres/commit', 3),
        ('Datastore/operation/Postgres/rollback', 1)]

@validate_transaction_metrics('test_database:test_execute_via_cursor',
        scoped_metrics=_test_execute_via_cursor_scoped_metrics,
        rollup_metrics=_test_execute_via_cursor_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_execute_via_cursor():
    with psycopg2.connect(
            database=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
            password=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']) as connection:

        cursor = connection.cursor()

        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, connection)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, cursor)

        cursor.execute("""drop table if exists datastore_psycopg2""")

        cursor.execute("""create table datastore_psycopg2 """
                """(a integer, b real, c text)""")

        cursor.executemany("""insert into datastore_psycopg2 """
                """values (%s, %s, %s)""", [(1, 1.0, '1.0'),
                (2, 2.2, '2.2'), (3, 3.3, '3.3')])

        cursor.execute("""select * from datastore_psycopg2""")

        for row in cursor:
            assert isinstance(row, tuple)

        cursor.execute("""update datastore_psycopg2 set a=%s, b=%s, """
                """c=%s where a=%s""", (4, 4.0, '4.0', 1))

        cursor.execute("""delete from datastore_psycopg2 where a=2""")

        connection.commit()

        cursor.callproc('now')
        cursor.callproc('pg_sleep', (0.25,))

        connection.rollback()
        connection.commit()

@validate_transaction_metrics('test_database:test_execute_via_cursor_dict',
        scoped_metrics=_test_execute_via_cursor_scoped_metrics,
        rollup_metrics=_test_execute_via_cursor_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_execute_via_cursor_dict():
    with psycopg2.connect(
            database=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
            password=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']) as connection:

        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, connection)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, cursor)

        cursor.execute("""drop table if exists datastore_psycopg2""")

        cursor.execute("""create table datastore_psycopg2 """
                """(a integer, b real, c text)""")

        cursor.executemany("""insert into datastore_psycopg2 """
                """values (%s, %s, %s)""", [(1, 1.0, '1.0'),
                (2, 2.2, '2.2'), (3, 3.3, '3.3')])

        cursor.execute("""select * from datastore_psycopg2""")

        for row in cursor:
            assert isinstance(row, dict)

        cursor.execute("""update datastore_psycopg2 set a=%s, b=%s, """
                """c=%s where a=%s""", (4, 4.0, '4.0', 1))

        cursor.execute("""delete from datastore_psycopg2 where a=2""")

        connection.commit()

        cursor.callproc('now')
        cursor.callproc('pg_sleep', (0.25,))

        connection.rollback()
        connection.commit()

_test_rollback_on_exception_scoped_metrics = [
        ('Function/psycopg2:connect', 1),
        ('Function/psycopg2.extensions:connection.__enter__', 1),
        ('Function/psycopg2.extensions:connection.__exit__', 1),
        ('Datastore/operation/Postgres/rollback', 1)]

_test_rollback_on_exception_rollup_metrics = [
        ('Datastore/all', 2),
        ('Datastore/allOther', 2),
        ('Datastore/Postgres/all', 2),
        ('Datastore/Postgres/allOther', 2),
        ('Datastore/operation/Postgres/rollback', 1)]

@validate_transaction_metrics('test_database:test_rollback_on_exception',
        scoped_metrics=_test_rollback_on_exception_scoped_metrics,
        rollup_metrics=_test_rollback_on_exception_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_rollback_on_exception():
    try:
        with psycopg2.connect(
                database=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
                password=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
                port=DB_SETTINGS['port']) as connection:

            raise RuntimeError('error')
    except RuntimeError:
        pass

@pytest.mark.skipif(POSTGRESQL_VERSION < (9, 2),
        reason="JSON data type was introduced in Postgres 9.2")
@validate_transaction_metrics('test_database:test_register_json',
        background_task=True)
@validate_transaction_errors(errors=[])
@background_task()
def test_register_json():
    with psycopg2.connect(
            database=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
            password=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']) as connection:

        cursor = connection.cursor()

        loads = lambda x: json.loads(x, parse_float=Decimal)
        psycopg2.extras.register_json(connection, loads=loads)
        psycopg2.extras.register_json(cursor, loads=loads)

@pytest.mark.skipif(POSTGRESQL_VERSION < (9, 2),
        reason="Range types were introduced in Postgres 9.2")
@validate_transaction_metrics('test_database:test_register_range',
        background_task=True)
@validate_transaction_errors(errors=[])
@background_task()
def test_register_range():
    with psycopg2.connect(
            database=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
            password=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']) as connection:

        create_sql = ('CREATE TYPE floatrange AS RANGE ('
                      'subtype = float8,'
                      'subtype_diff = float8mi)')

        cursor = connection.cursor()

        cursor.execute("DROP TYPE if exists floatrange")
        cursor.execute(create_sql)

        psycopg2.extras.register_range('floatrange',
                psycopg2.extras.NumericRange, connection)

        cursor.execute("DROP TYPE if exists floatrange")
        cursor.execute(create_sql)

        psycopg2.extras.register_range('floatrange',
                psycopg2.extras.NumericRange, cursor)

        cursor.execute("DROP TYPE if exists floatrange")
