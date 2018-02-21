import logging
import os
import shutil

import psycopg2
import VampireDefaults
try:
    import ArcGISServerImpl
except ImportError:
    pass
logger = logging.getLogger(__name__)

class GISServer():
    subclasses = {}

    @classmethod
    def register_subclass(cls, server_type):
        def decorator(subclass):
            cls.subclasses[server_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, server_type, vampire_defaults=None):
        if server_type not in cls.subclasses:
            raise ValueError('Bad server type {}'.format(server_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[server_type](vp)

@GISServer.register_subclass('geoserver')
class Geoserver(object):
    def __init__(self, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.vp = vampire_defaults
        return

    def publish(self, product):
        self.move_output_to_geoserver(product)
        self.upload_to_db(product)
        return

    def move_output_to_geoserver(self, product):
        _geoserver_data = self.vp.get('directories', 'geoserver_data') #'C:\\Program Files (x86)\\GeoServer 2.11.0\\data_dir\\data\\'
        if os.path.exists(product.product_filename):
            # copy to geoserver data dir
            _dst_dir = os.path.join(_geoserver_data, product.destination_filename)
            print product.product_name
            print product.product_filename
            print product.product_dir
            print product.destination_filename
            print _dst_dir

            shutil.copyfile(os.path.join(product.product_dir, product.product_filename),
                            os.path.join(_geoserver_data, product.destination_filename))
        return None

    def upload_to_db(self, product):
        try:
            _db_name = self.vp.get('database', '{0}_db'.format(product.product_name.lower()))
        except Exception, e:
            _db_name = self.vp.get('database', 'default_db')
        try:
            _schema = self.vp.get('database', '{0}_schema'.format(product.product_name.lower()))
        except Exception, e:
            _schema = self.vp.get('database', 'default_schema')
        try:
            _host = self.vp.get('database', '{0}_host'.format(product.product_name.lower()))
        except Exception, e:
            _host = self.vp.get('database', 'default_host')
        try:
            _port = self.vp.get('database', '{0}_port'.format(product.product_name.lower()))
        except Exception, e:
            _port = self.vp.get('database', 'default_port')
        try:
            _user = self.vp.get('database', '{0}_user'.format(product.product_name.lower()))
        except Exception, e:
            _user = self.vp.get('database', 'default_user')
        try:
            _pw = self.vp.get('database', '{0}_pw'.format(product.product_name.lower()))
        except Exception, e:
            _pw = self.vp.get('database', 'default_pw')
        try:
            _table_name = '{0}.{1}'.format(_schema, self.vp.get('database',
                                                                '{0}_table'.format(product.product_name.lower())))
        except Exception, e:
            raise ValueError("Database table name not in Vampire.ini")

        print product.ingestion_date
        _ingestion_date = product.ingestion_date.replace(hour=6)
        print _ingestion_date
        # create connection to database
        _connection_str = 'dbname={0} host={1} user={2} password={3}'.format(_db_name, _host, _user, _pw)
        _conn = psycopg2.connect(_connection_str)
        _cur = _conn.cursor()
        try:
            _cur.execute(
                """INSERT INTO %(table)s (the_geom, location, ingestion)
    SELECT the_geom, %(location)s, %(ingestion)s
    FROM %(table2)s
    WHERE fid = 1 AND NOT EXISTS (SELECT location, ingestion FROM %(table3)s WHERE %(table3)s.location = %(location)s
                                  AND %(table3)s.ingestion = %(ingestion)s)
    """,
                {'table':psycopg2.extensions.AsIs(_table_name), 'location':product.destination_filename, 'ingestion':_ingestion_date,
                 'table2':psycopg2.extensions.AsIs(_table_name), 'table3':psycopg2.extensions.AsIs(_table_name)})
        except Exception, e:
            print "Error: Can't INSERT into table {0}".format(_table_name)
            print e.message
        _conn.commit()
        return None

try:
    import arcpy

    @GISServer.register_subclass('arcgis')
    class ArcGISServer(object):
        def __init__(self, vampire_defaults):
            logger.debug('Initialising MODIS download task')
            self.vp = vampire_defaults
            self.server = ArcGISServerImpl.ArcGISServerImpl(self.vp)
            return

        def publish(self, product):
            self.server.publish(product)
            return

except ImportError, e:
    logger.info("arcpy not available")