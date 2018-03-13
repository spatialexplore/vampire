import ast
import itertools

import pandas
import psycopg2
import sqlalchemy

def check_table_empty(database, host, user, password, table_name):
    # create connection to database
    _connection_str = 'dbname={0} host={1} user={2} password={3}'.format(database, host, user, password)
    _conn = psycopg2.connect(_connection_str)
    _cur = _conn.cursor()
    _cur.execute("select count(*) as tot from {0}".format(table_name,))
    result = _cur.fetchone()[0]
    _conn.close()
    if result == 0:
        return True
    return False

def check_table_exists(database, host, user, password, table_name):
    # create connection to database
    _connection_str = 'dbname={0} host={1} user={2} password={3}'.format(database, host, user, password)
    _conn = psycopg2.connect(_connection_str)
    _cur = _conn.cursor()
    _cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (table_name,))
    result = _cur.fetchone()[0]
    _conn.close()
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
#    print pd
    engine = sqlalchemy.create_engine(_url)
    _exists = True
    # check if table exists first
    if check_table_exists(database=database, host=host, user=user, password=password, table_name=table):
        if not check_table_empty(database=database, host=host, user=user, password=password,
                                 table_name=table):
            index_name = list(pd.columns.values)[0].upper()
            max_id_query = 'select max(index) FROM {0}.{1}'.format(schema, table)
            max_id = int(pandas.read_sql_query(max_id_query, engine).values)
            pd['index'] = range(max_id + 1, max_id + len(pd) + 1)
        else:
            pd['index'] = range(1, len(pd) + 1)
    else:
        _exists = False
        pd['index'] = range(1, len(pd) + 1)

    if _exists and overwrite:
        # find rows and delete them first
        to_sql_update(pd, engine, schema, table)
#        try:
#            _lock_query = 'lock tables public.{0} write'.format(table)
#            engine.execute(_lock_query)
###        pd.to_sql(table, engine, if_exists='replace', index=False)
#        finally:
#            engine.execute('unlock tables')
#        pd.to_sql(table, engine, if_exists='replace', index=True)
    else:
#        try:
#            _lock_query = 'lock tables `{0}` write'.format(table)
#            engine.execute(_lock_query)
        pd.to_sql(table, engine, if_exists='append', index=False)
#        finally:
#            engine.execute('unlock tables')
#        pd.to_sql(table, engine, if_exists='append', index=True)

    return None

def to_sql_update(df, engine, schema, table):
    sql_primary_keys = '''SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
              FROM pg_index i
              JOIN pg_attribute a ON a.attrelid = i.indrelid
                      AND a.attnum = ANY(i.indkey)
              WHERE i.indrelid = '{table}'::regclass
              AND i.indisprimary;'''.format(table=table)
    id_cols = [x[0] for x in engine.execute(sql_primary_keys)]
    id_vals = [df[col_name].tolist() for col_name in id_cols]
    sql = '''DELETE FROM {schema}.{table} WHERE FALSE'''.format(schema=schema, table=table)
    for row in zip(*id_vals):
        sql_row = ' AND '.join([''' {} = '{}' '''.format(n, v) for n, v in zip(id_cols, row)])
        sql += ' OR ({}) '.format(sql_row)
    engine.execute(sql)

    df.to_sql(table, engine, schema=schema, if_exists='append', index=False)
    return