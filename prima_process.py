
import sys
import psycopg2
import datetime
import dateutil
import time
import optparse
import traceback
import os
import shutil
import csv
import vampire.config_generator
import vampire.ConfigProcessor
import vampire.VampireDefaults
import vampire.database_utils
import vampire.directory_utils
import vampire.filename_utils
import vampire.csv_utils


def upload_impact_to_db(product, impact_type, start_date, vp):
    if product == 'vhi':
        _product_dir = vp.get('hazard_impact', 'vhi_output_dir')
        if impact_type == 'area':
            _filename_pattern = vp.get('hazard_impact', 'vhi_area_pattern')
            _table_name = 'vhi_area'
#        _product_filename = os.path.join(_product_dir,
#                                         'lka_phy_MOD13Q1.%s.250m_16_days_vhi_area_dsd.csv' % start_date.strftime(
#                                             '%Y.%m.%d'))
        elif impact_type == 'popn':
            _filename_pattern = vp.get('hazard_impact', 'vhi_popn_pattern')
            _table_name = 'vhi_popn'
        else:
            raise ValueError('Invalid impact type {0}'.format(impact_type))
        _filename_pattern = _filename_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(start_date.year))
        _filename_pattern = _filename_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(start_date.month))
        _filename_pattern = _filename_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(start_date.day))
        _filenames = vampire.directory_utils.get_matching_files(_product_dir, _filename_pattern)
        _product_filename = _filenames[0]

        _database = 'prima_impact'
        _host = 'localhost'
        _user = 'prima_user'
        _password = 'prima_user'
        _port = 5432
        vampire.database_utils.insert_csv_to_table(_database, _host, _port, _user, _password, _table_name,
                                                   _product_filename)
    return None


def convert_csv_to_choropleth(product, impact_type, start_date, vp):
    if product.lower() == 'vhi':
        _product_dir = vp.get('hazard_impact', 'vhi_output_dir')
        if impact_type == 'area':
            _filename_pattern = vp.get('hazard_impact', 'vhi_area_pattern')
            _filename_pattern = _filename_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(start_date.year))
            _filename_pattern = _filename_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(start_date.month))
            _filename_pattern = _filename_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(start_date.day))
            _filenames = vampire.directory_utils.get_matching_files(_product_dir, _filename_pattern)
            _product_filename = _filenames[0]
            #            _product_filename = os.path.join(_product_dir,
            #                                        'lka_phy_MOD13Q1.%s.250m_16_days_vhi_area_dsd.csv' % start_date.strftime('%Y.%m.%d'))
            _field_name = 'area_aff'
            _output_pattern = vp.get('hazard_impact', 'vhi_area_output_pattern')
            _output_filename = vampire.filename_utils.generate_output_filename(os.path.basename(_product_filename),
                                                                               _filename_pattern, _output_pattern)
            #            _output_filename = 'lka_phy_MOD13Q1.%s.vhi_impact_dsd_area.csv' % start_date.strftime('%Y.%m.%d')
            _output_filename = os.path.join(_product_dir, _output_filename)
        elif impact_type == 'popn':
            _filename_pattern = vp.get('hazard_impact', 'vhi_popn_pattern')
            _filename_pattern = _filename_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(start_date.year))
            _filename_pattern = _filename_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(start_date.month))
            _filename_pattern = _filename_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(start_date.day))
            _filenames = vampire.directory_utils.get_matching_files(_product_dir, _filename_pattern)
            _product_filename = _filenames[0]
            # _product_filename = os.path.join(_product_dir,
            #                             'lka_phy_MOD13Q1.%s.250m_16_days_vhi_popn_dsd.csv' % start_date.strftime('%Y.%m.%d'))
            _field_name = 'pop_aff'
            _output_pattern = vp.get('hazard_impact', 'vhi_popn_output_pattern')
            _output_filename = vampire.filename_utils.generate_output_filename(os.path.basename(_product_filename),
                                                                               _filename_pattern, _output_pattern)
#            _output_filename = 'lka_phy_MOD13Q1.%s.vhi_impact_dsd_popn.csv' % start_date.strftime('%Y.%m.%d')
#            _output_filename = os.path.join(_product_dir, _output_filename)
        else:
            raise ValueError('ERROR: Impact type {0} not recognised.'.format(impact_type))
        vampire.csv_utils.csv_to_choropleth_format(_product_filename, _output_filename,
                                                   'dsd_n', _field_name, 'start_date', 'end_date')
    else:
        return None
    return _output_filename

def move_output_to_geoserver(product, start_date, vp):
    _geoserver_data = 'C:\\Program Files (x86)\\GeoServer 2.11.0\\data_dir\\data\\'
    if product.lower() == 'rainfall_anomaly':
        # rainfall anomaly
        _product_dir = vp.get('CHIRPS_Rainfall_Anomaly', 'output_dir')
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
        _product_dir = vp.get('MODIS_VHI', 'vhi_product_dir')
        _product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % start_date.strftime('%Y.%m.%d')
        _product_name = 'vhi' #os.path.join('vhi', _product_filename)
        _dst_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % start_date.strftime('%Y%m%d')
    elif product.lower() == 'spi':
        _product_dir = vp.get('CHIRPS_SPI', 'output_dir')
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

def upload_to_db(product, start_date):
    _schema = 'public'
    _date_string = start_date.strftime('%Y%m%d')
    if product.lower() == 'rainfall_anomaly':
        # rainfall anomaly
        _db_name = 'prima_ra'
        _table_name = 'rainfall_anomaly'
        _filename = 'lka_cli_chirps-v2.0.%s.ratio_anom.tif' % _date_string
    elif product.lower() == 'vhi':
        _db_name = 'prima_vhi_250m'
        _table_name = 'public.vhi'
#        _filename = 'lka_phy_MOD13Q1.20160321.250m_16_days_EVI_EVI_VCI_VHI.tif'
        _filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % _date_string
    elif product.lower() == 'spi':
        _db_name = 'prima_spi_10day'
        _table_name = 'public.spi'
        _filename = 'lka_cli_chirps-v2.0.%s.spi.tif' % _date_string
    else:
        raise ValueError, 'Product {0} is not a valid product (ra, vhi, spi)'.format(product)

    _ingestion_date = start_date #datetime.datetime.strptime(start_date, '%Y-%m-%d')
    print _ingestion_date
    _ingestion_date = _ingestion_date.replace(hour=6)
    print _ingestion_date
    # create connection to database
    _connection_str = 'dbname={0} host={1} user={2} password={3}'.format(_db_name, 'localhost', 'prima_user', 'prima_user')
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


def main():
    try:
        start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        parser.add_option('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option('-c', '--country', dest='country', action='store', help='country name')
        parser.add_option('-p', '--product', dest='product', action='store', help='product')
        parser.add_option('-o', '--output', dest='output', action='store', help='output filename')
        parser.add_option('-i', '--interval', dest='interval', action='store', help='interval')
        parser.add_option('-d', '--start_date', dest='start_date', action='store', help='start year-month')
        (options, args) = parser.parse_args()
        #if len(args) < 1:
        #    parser.error ('missing argument')
        params = {}
        if options.verbose: print time.asctime()
        _country = None
        if options.country:
            _country = options.country
            print 'country=', _country
            params['country'] = _country
        _product = None
        if options.product:
            _product = options.product
            print 'product=', _product
            params['product'] = _product
        _output = None
        if options.output:
            _output = options.output
            print 'output=', _output
        _interval = None
        if options.interval:
            _interval = options.interval
            print 'interval=', _interval
            params['interval'] = _interval
        _start_date = None
        if options.start_date:
            try:
                _start_date = datetime.datetime.strptime(options.start_date, "%Y-%m")
            except ValueError:
                # can't parse string, try with day as well
                _start_date = datetime.datetime.strptime(options.start_date, "%Y-%m-%d")
            print 'start_date=', _start_date
            params['start_date'] = _start_date
        params['impact'] = True
        vampire.config_generator.generate_config_file(_output, params)
        vp = vampire.VampireDefaults.VampireDefaults()
        cp = vampire.ConfigProcessor.ConfigProcessor()
        cp.process_config(_output, vp.logger)
        move_output_to_geoserver(_product, _start_date, vp)
        upload_to_db(product=_product, start_date=_start_date)
        convert_csv_to_choropleth(product=_product, impact_type='area', start_date=_start_date, vp=vp)
        upload_impact_to_db(product=_product, impact_type='area', start_date=_start_date, vp=vp)
        convert_csv_to_choropleth(product=_product, impact_type='popn', start_date=_start_date, vp=vp)
        upload_impact_to_db(product=_product, impact_type='popn', start_date=_start_date, vp=vp)

        # vampire.database_utils.insert_csv_to_table(database='prima_impact', host='localhost', user='prima_user',
        #                                            password='prima_user', table='vhi_area', csv_file='')

        if options.verbose: print time.asctime()
        if options.verbose: print 'TOTAL TIME IN MINUTES:',
        if options.verbose: print (time.time() - start_time) / 60.0
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)

if __name__ == '__main__':
    main()
