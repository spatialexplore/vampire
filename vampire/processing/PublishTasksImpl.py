import logging

import GISServer
import PublishProductTasksImpl
import directory_utils
import database_utils
import VampireDefaults

logger = logging.getLogger(__name__)

class PublishTasksImpl():
    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, process_type, params, vampire_defaults=None):
        if process_type not in cls.subclasses:
            raise ValueError('Bad process type {}'.format(process_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[process_type](params, vp)

@PublishTasksImpl.register_subclass('gis_server')
class PublishToGISServerTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising publish to GIS server task')
        self.params = params
        self.vp = vampire_defaults
        self.product = PublishProductTasksImpl.PublishProductTasksImpl.create(self.params['product'].lower(),
                                                                              self.params, self.vp)
        self.server = GISServer.GISServer.create(self.vp.get('vampire', 'gis_server').lower(), self.vp)
        return

    def process(self):
        self.server.publish(self.product)
#        self.move_output_to_gisserver()
#        self.upload_to_db()
        return




@PublishTasksImpl.register_subclass('database')
class PublishToDatabaseTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising publish to database task')
        self.params = params
        self.vp = vampire_defaults
        self.product = PublishProductTasksImpl.PublishProductTasksImpl.create(self.params['product'].lower(),
                                                                              self.params, self.vp)
        return

    def process(self):
        self.upload_impact_to_db(self.product)
        return

    def upload_impact_to_db(self, product): #, impact_type, start_date, vp
        try:
            _host = self.vp.get('database', 'impact_host') #'localhost'
        except Exception,e:
            _host = self.vp.get('database', 'default_host')
        try:
            _user = self.vp.get('database', 'impact_user') #'localhost'
        except Exception,e:
            _user = self.vp.get('database', 'default_user')
        try:
            _password = self.vp.get('database', 'impact_pw') #'localhost'
        except Exception,e:
            _password = self.vp.get('database', 'default_pw')
        try:
            _port = self.vp.get('database', 'impact_port') #'localhost'
        except Exception,e:
            _port = self.vp.get('database', 'default_port')
        _overwrite = False
        if 'overwrite' in self.params:
            _overwrite = True
        database_utils.insert_csv_to_table(database=product.database, host=_host, port=_port, user=_user,
                                                   password=_password, table=product.table_name, schema=product.schema,
                                                   csv_file=product.product_filename, overwrite=_overwrite)
    #     _product_dir = product.product_dir
    #     _filename_pattern = product.filename_pattern
    #     _table_name = product.table_name
    #
    #     if product == 'vhi':
    #         _product_dir = self.vp.get('hazard_impact', 'vhi_output_dir')
    #         if self.impact_type == 'area':
    #             _filename_pattern = self.vp.get('hazard_impact', 'vhi_area_pattern')
    #             _table_name = self.vp.get('database', 'impact_area_table') #'vhi_area'
    #             try:
    #                 _schema = self.vp.get('database', 'impact_area_schema')
    #             except Exception, e:
    #                 _schema = self.vp.get('database', 'default_schema')
    # #        _product_filename = os.path.join(_product_dir,
    # #                                         'lka_phy_MOD13Q1.%s.250m_16_days_vhi_area_dsd.csv' % start_date.strftime(
    # #                                             '%Y.%m.%d'))
    #         elif self.impact_type == 'popn':
    #             _filename_pattern = self.vp.get('hazard_impact', 'vhi_popn_pattern')
    #             _table_name = self.vp.get('database', 'impact_popn_table') #'vhi_popn'
    #             try:
    #                 _schema = self.vp.get('database', 'impact_popn_schema')
    #             except Exception, e:
    #                 _schema = self.vp.get('database', 'default_schema')
    #         elif self.impact_type == 'crops':
    #             _filename_pattern = self.vp.get('hazard_impact', 'vhi_crops_pattern')
    #             _table_name = self.vp.get('database', 'impact_crops_table') #'vhi_crops'
    #             try:
    #                 _schema = self.vp.get('database', 'impact_crops_schema')
    #             except Exception, e:
    #                 _schema = self.vp.get('database', 'default_schema')
    #         elif self.impact_type == 'poverty':
    #             _filename_pattern = self.vp.get('hazard_impact', 'vhi_poverty_pattern')
    #             _table_name = self.vp.get('database', 'impact_poverty_table')  # 'vhi_crops'
    #             try:
    #                 _schema = self.vp.get('database', 'impact_poverty_schema')
    #             except Exception, e:
    #                 _schema = self.vp.get('database', 'default_schema')
    #         else:
    #             raise ValueError('Invalid impact type {0}'.format(self.impact_type))
    #         _filename_pattern = _filename_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.start_date.year))
    #         _filename_pattern = _filename_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.start_date.month))
    #         _filename_pattern = _filename_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.start_date.day))
    #         _filenames = directory_utils.get_matching_files(_product_dir, _filename_pattern)
    #         if _filenames is not None:
    #             _product_filename = _filenames[0]
    #         else:
    #             _product_filename = None
    #             raise ValueError("No product filename found in upload_impact_to_db")
    #
    #         _database = self.vp.get('database', 'impact_db') #'prima_impact'
    #         try:
    #             _host = self.vp.get('database', 'impact_host') #'localhost'
    #         except Exception,e:
    #             _host = self.vp.get('database', 'default_host')
    #         try:
    #             _user = self.vp.get('database', 'impact_user') #'localhost'
    #         except Exception,e:
    #             _user = self.vp.get('database', 'default_user')
    #         try:
    #             _password = self.vp.get('database', 'impact_pw') #'localhost'
    #         except Exception,e:
    #             _password = self.vp.get('database', 'default_pw')
    #         try:
    #             _port = self.vp.get('database', 'impact_port') #'localhost'
    #         except Exception,e:
    #             _port = self.vp.get('database', 'default_port')
    #         database_utils.insert_csv_to_table(database=_database, host=_host, port=_port, user=_user,
    #                                                    password=_password, table=_table_name, schema=_schema,
    #                                                    csv_file=_product_filename) #, overwrite=True)
        return None
