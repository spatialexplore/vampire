import psycopg2
import datetime
import os
import shutil

# class GeoserverManager(GISServerManager.GISServerManager):
#
#     def __init__(self, gis_server_type):
#         GISServerManager.GISServerManager.__init__(self, gis_server_type)
#         return

def upload_to_GIS_server(product, start_date, vp):
    move_output_to_geoserver(product=product, start_date=start_date, vp=vp)
    upload_to_db(product=product, start_date=start_date, vp=vp)

def move_output_to_geoserver(product, start_date, vp):
    _geoserver_data = vp.vampire.get('directories', 'geoserver_data') #'C:\\Program Files (x86)\\GeoServer 2.11.0\\data_dir\\data\\'
    if product.lower() == 'rainfall_anomaly':
        # rainfall anomaly
        _product_dir = vp.vampire.get('CHIRPS_Rainfall_Anomaly', 'output_dir')
        if start_date.day < 11:
            _dekad = 1
        elif start_date.day < 21:
            _dekad = 2
        else:
            _dekad = 3
        _date_string = '{0}.{1}'.format(start_date.strftime('%Y.%m'), _dekad)
        _product_filename = 'lka_cli_chirps-v2.0.%s.ratio_anom.tif' % _date_string
        _product_name = 'rainfall_anomaly' #os.path.join('rainfall_anomaly', _product_filename)
        _dst_filename = 'lka_cli_chirps-v2.0.%s.ratio_anom.tif' % start_date.strftime('%Y%m%d')
    elif product.lower() == 'vhi':
        _product_dir = vp.vampire.get('MODIS_VHI', 'vhi_product_dir')
        _product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % start_date.strftime('%Y.%m.%d')
        _product_name = 'vhi' #os.path.join('vhi', _product_filename)
        _dst_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % start_date.strftime('%Y%m%d')
    elif product.lower() == 'vhi_masked':
        _product_dir = vp.vampire.get('MODIS_VHI', 'vhi_product_dir')
        _product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI_cropmask.tif' % start_date.strftime('%Y.%m.%d')
        _product_name = 'vhi_mask'  # os.path.join('vhi', _product_filename)
        _dst_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI_masked.tif' % start_date.strftime('%Y%m%d')
    elif product.lower() == 'spi':
        _product_dir = vp.vampire.get('CHIRPS_SPI', 'output_dir')
        if start_date.day < 11:
            _dekad = 1
        elif start_date.day < 21:
            _dekad = 2
        else:
            _dekad = 3
        _date_string = '{0}.{1}'.format(start_date.strftime('%Y.%m'), _dekad)
        _product_filename = 'lka_cli_chirps-v2.0.%s.spi.tif' % _date_string
        _product_name = 'spi' #os.path.join('spi', _product_filename)
        _dst_filename = 'lka_cli_chirps-v2.0.%s.spi.tif' % start_date.strftime('%Y%m%d')
    else:
        raise ValueError, 'Product {0} is not a valid product (ra, vhi, spi)'.format(product)
    if os.path.exists(os.path.join(_product_dir, _product_filename)):
        # copy to geoserver data dir
        _dst_dir = os.path.join(_geoserver_data, _product_name)
        print _product_name
        print _product_filename
        print _product_dir
        print _dst_filename
        print _dst_dir
        shutil.copyfile(os.path.join(_product_dir, _product_filename),
                        os.path.join(_dst_dir, _dst_filename))
    return None

def upload_to_db(product, start_date, vp):
    try:
        _db_name = vp.vampire.get('database', '{0}_db'.format(product.lower()))
    except Exception, e:
        _db_name = vp.vampire.get('database', 'default_db')
    try:
        _schema = vp.vampire.get('database', '{0}_schema'.format(product.lower()))
    except Exception, e:
        _schema = vp.vampire.get('database', 'default_schema')
    try:
        _host = vp.vampire.get('database', '{0}_host'.format(product.lower()))
    except Exception, e:
        _host = vp.vampire.get('database', 'default_host')
    try:
        _port = vp.vampire.get('database', '{0}_port'.format(product.lower()))
    except Exception, e:
        _port = vp.vampire.get('database', 'default_port')
    try:
        _user = vp.vampire.get('database', '{0}_user'.format(product.lower()))
    except Exception, e:
        _user = vp.vampire.get('database', 'default_user')
    try:
        _pw = vp.vampire.get('database', '{0}_pw'.format(product.lower()))
    except Exception, e:
        _pw = vp.vampire.get('database', 'default_pw')
    try:
        _table_name = '{0}.{1}'.format(_schema, vp.vampire.get('database', '{0}_table'.format(product.lower())))
    except Exception, e:
        raise ValueError("Database table name not in Vampire.ini")

    _date_string = start_date.strftime('%Y%m%d')
    if product.lower() == 'rainfall_anomaly':
        # rainfall anomaly
#        _db_name = vp.get('database', 'default_db') #'prima_ra'
#        _table_name = 'rainfall_anomaly'
        _filename = 'lka_cli_chirps-v2.0.%s.ratio_anom.tif' % _date_string
        _ingestion_date = start_date - datetime.timedelta(days=int(vp.vampire.get('CHIRPS_Rainfall_Anomaly', 'interval')))
    elif product.lower() == 'vhi':
#        _db_name = 'prima_vhi_250m'
#        _table_name = 'public.vhi'
#        _filename = 'lka_phy_MOD13Q1.20160321.250m_16_days_EVI_EVI_VCI_VHI.tif'
        _filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % _date_string
        _ingestion_date = start_date - datetime.timedelta(days=int(vp.vampire.get('MODIS_VHI', 'interval')))
    elif product.lower() == 'vhi_masked':
        _filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI_masked.tif' % _date_string
        _ingestion_date = start_date - datetime.timedelta(days=int(vp.vampire.get('MODIS_VHI', 'interval')))
    elif product.lower() == 'spi':
#        _db_name = 'prima_spi_10day'
#        _table_name = 'public.spi'
        _filename = 'lka_cli_chirps-v2.0.%s.spi.tif' % _date_string
        _ingestion_date = start_date - datetime.timedelta(days=int(vp.vampire.get('CHIRPS_SPI', 'interval')))
    else:
        raise ValueError, 'Product {0} is not a valid product (ra, vhi, spi)'.format(product)

#    _ingestion_date = start_date #datetime.datetime.strptime(start_date, '%Y-%m-%d')
    print _ingestion_date
    _ingestion_date = _ingestion_date.replace(hour=6)
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
            {'table':psycopg2.extensions.AsIs(_table_name), 'location':_filename, 'ingestion':_ingestion_date,
             'table2':psycopg2.extensions.AsIs(_table_name), 'table3':psycopg2.extensions.AsIs(_table_name)})
#         """INSERT INTO %(table)s (the_geom, location, ingestion)
# SELECT the_geom, %(location)s, %(ingestion)s
# FROM %(table2)s
# WHERE fid = 1""",
#         {'table': psycopg2.extensions.AsIs(_table_name), 'location': _filename, 'ingestion': _ingestion_date,
#          'table2': psycopg2.extensions.AsIs(_table_name)})
    except Exception, e:
        print "Error: Can't INSERT into table {0}".format(_table_name)
        print e.message
    _conn.commit()
    return None
