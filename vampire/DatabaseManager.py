import VampireDefaults
import database_utils
import directory_utils

class DatabaseManager:
    'Base Class for managing uploading of products to database'

    def __init__(self):
        # load default values from .ini file
        self.vampire = VampireDefaults.VampireDefaults()
        return

    def upload_to_database(self, product, start_date, end_date):
        self._upload_impact_to_db(product=product, impact_type='area', start_date=start_date)


    def _upload_impact_to_db(self, product, impact_type, start_date):
        if product == 'vhi':
            _product_dir = self.vampire.get('hazard_impact', 'vhi_output_dir')
            if impact_type == 'area':
                _filename_pattern = self.vampire.get('hazard_impact', 'vhi_area_pattern')
                _table_name = self.vampire.get('database', 'impact_area_table') #'vhi_area'
                try:
                    _schema = self.vampire.get('database', 'impact_area_schema')
                except Exception, e:
                    _schema = self.vampire.get('database', 'default_schema')
    #        _product_filename = os.path.join(_product_dir,
    #                                         'lka_phy_MOD13Q1.%s.250m_16_days_vhi_area_dsd.csv' % start_date.strftime(
    #                                             '%Y.%m.%d'))
            elif impact_type == 'popn':
                _filename_pattern = self.vampire.get('hazard_impact', 'vhi_popn_pattern')
                _table_name = self.vampire.get('database', 'impact_popn_table') #'vhi_popn'
                try:
                    _schema = self.vampire.get('database', 'impact_popn_schema')
                except Exception, e:
                    _schema = self.vampire.get('database', 'default_schema')
            elif impact_type == 'crops':
                _filename_pattern = self.vampire.get('hazard_impact', 'vhi_crops_pattern')
                _table_name = self.vampire.get('database', 'impact_crops_table') #'vhi_crops'
                try:
                    _schema = self.vampire.get('database', 'impact_crops_schema')
                except Exception, e:
                    _schema = self.vampire.get('database', 'default_schema')
            elif impact_type == 'poverty':
                _filename_pattern = self.vampire.get('hazard_impact', 'vhi_poverty_pattern')
                _table_name = self.vampire.get('database', 'impact_poverty_table')  # 'vhi_crops'
                try:
                    _schema = self.vampire.get('database', 'impact_poverty_schema')
                except Exception, e:
                    _schema = self.vampire.get('database', 'default_schema')
            else:
                raise ValueError('Invalid impact type {0}'.format(impact_type))
            _filename_pattern = _filename_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(start_date.year))
            _filename_pattern = _filename_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(start_date.month))
            _filename_pattern = _filename_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(start_date.day))
            _filenames = vampire.directory_utils.get_matching_files(_product_dir, _filename_pattern)
            if _filenames is not None:
                _product_filename = _filenames[0]
            else:
                _product_filename = None
                raise ValueError("No product filename found in upload_impact_to_db")

            _database = self.vampire.get('database', 'impact_db') #'prima_impact'
            try:
                _host = self.vampire.get('database', 'impact_host') #'localhost'
            except Exception,e:
                _host = self.vampire.get('database', 'default_host')
            try:
                _user = self.vampire.get('database', 'impact_user') #'localhost'
            except Exception,e:
                _user = self.vampire.get('database', 'default_user')
            try:
                _password = self.vampire.get('database', 'impact_pw') #'localhost'
            except Exception,e:
                _password = self.vampire.get('database', 'default_pw')
            try:
                _port = self.vampire.get('database', 'impact_port') #'localhost'
            except Exception,e:
                _port = self.vampire.get('database', 'default_port')
            vampire.database_utils.insert_csv_to_table(database=_database, host=_host, port=_port, user=_user,
                                                       password=_password, table=_table_name, schema=_schema,
                                                       csv_file=_product_filename) #, overwrite=True)
        return None
