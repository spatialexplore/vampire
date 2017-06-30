import sys
import pandas
import sqlalchemy
import psycopg2
import itertools
import ast
import csv
import datetime
import dateutil
import time
import optparse
import traceback
import os
import shutil
import vampire.config_generator
import vampire.ConfigProcessor
import vampire.VampireDefaults

def check_table_exists(database, host, user, password, table_name):
    # create connection to database
    _connection_str = 'dbname={0} host={1} user={2} password={3}'.format(database, host, user, password)
    _conn = psycopg2.connect(_connection_str)
    _cur = _conn.cursor()
    _cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (table_name,))
    result = _cur.fetchone()[0]
    return result

def create_table(database, table_name, columns, host, user, password):
    # create connection to database
    _connection_str = 'dbname={0} host={1} user={2} password={3}'.format(database, host, user, password)
    _conn = psycopg2.connect(_connection_str)
    _cur = _conn.cursor()
    # set up create table string with fields and field types
    _create_string = 'CREATE TABLE {0} ('.format(table_name)
    for i in columns:
        _create_string = _create_string + '{0} {1},'.format(i[0], i[1])
    # remove final ','
    _create_string = _create_string[:-1]
    _create_string = _create_string + ');'
    _cur.execute(_create_string)
    _conn.commit()
    _cur.close()
    _conn.close()
    return None

def get_fieldnames(csvFile):
    """
    Read the first row and store values in a tuple
    """
    with open(csvFile) as csvfile:
        firstRow = csvfile.readlines(1)
        fieldnames = tuple(firstRow[0].strip('\n').split("\t"))
    return fieldnames

def write_cursor(csvFile, fieldnames):
    """
    Convert csv rows into an array of dictionaries
    All data types are automatically checked and converted
    """
    cursor = []  # Placeholder for the dictionaries/documents
    with open(csvFile) as csvFile:
        for row in itertools.islice(csvFile, 1, None):
            values = list(row.strip('\n').split("\t"))
            for i, value in enumerate(values):
                nValue = ast.literal_eval(value)
                values[i] = nValue
            cursor.append(dict(zip(fieldnames, values)))
    return cursor

def insert_csv_to_table(database, host, port, user, password, schema, table, csv_file, overwrite=False, index=True):
    _url = 'postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database)
    pd = pandas.read_csv(csv_file)
    print pd
    engine = sqlalchemy.create_engine(_url)
    if overwrite:
#        try:
#            _lock_query = 'lock tables public.{0} write'.format(table)
#            engine.execute(_lock_query)
        max_id_query = 'select max(index) FROM {0}.{1}'.format(schema, table)
        max_id = int(pandas.read_sql_query(max_id_query, engine).values)
        pd['index'] = range(max_id + 1, max_id + len(pd) + 1)
        pd.to_sql(table, engine, if_exists='replace', index=False)
#        finally:
#            engine.execute('unlock tables')
#        pd.to_sql(table, engine, if_exists='replace', index=True)
    else:
#        try:
#            _lock_query = 'lock tables `{0}` write'.format(table)
#            engine.execute(_lock_query)
        max_id_query = 'select max(index) FROM {0}.{1}'.format(schema, table)
        max_id = int(pandas.read_sql_query(max_id_query, engine).values)
        pd['index'] = range(max_id + 1, max_id + len(pd) + 1)
        pd.to_sql(table, engine, if_exists='append', index=False)
#        finally:
#            engine.execute('unlock tables')
#        pd.to_sql(table, engine, if_exists='append', index=True)
    #
    # # create connection to database
    # _connection_str = 'dbname={0} host={1} user={2} password={3}'.format(database, host, user, password)
    # _conn = psycopg2.connect(_connection_str)
    # _cur = _conn.cursor()
    # _fieldnames = get_fieldnames(csv_file)
    # _write_cursor = write_cursor(csv_file, _fieldnames)
    #
    # _sql_statement = """
    #     COPY %s FROM STDIN WITH
    #         CSV
    #         HEADER
    #         DELIMITER AS ','
    #     """
    # _cur.copy_expert(sql=_sql_statement % table, file=csv_file)
    #
    # _conn.commit()
    # _cur.close()
    # _conn.close()
    return None

