import datetime
import logging
import directory_utils
import re
import os

import VampireDefaults

logger = logging.getLogger(__name__)


class PublishProductTasksImpl(object):
    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, product_type, params, vampire_defaults=None):
        if product_type not in cls.subclasses:
            raise ValueError('Bad product type {}'.format(product_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[product_type](params, vp)

class PublishableProduct(object):
    def __init__(self):
        self.product_dir = None
        self.product_name = None
        self.product_filename = None
        self.destination_filename = None
        self.ingestion_date = None
        self.valid_from_date = None
        self.valid_to_date = None
        return

    @property
    def product_dir(self):
        return self.__product_dir
    @product_dir.setter
    def product_dir(self, op):
        self.__product_dir = op

    @property
    def product_name(self):
        return self.__product_name
    @product_name.setter
    def product_name(self, op):
        self.__product_name = op

    @property
    def product_filename(self):
        return self.__product_filename
    @product_filename.setter
    def product_filename(self, op):
        self.__product_filename = op

    @property
    def destination_filename(self):
        return self.__destination_filename
    @destination_filename.setter
    def destination_filename(self, op):
        self.__destination_filename = op

    @property
    def ingestion_date(self):
        return self.__ingestion_date
    @ingestion_date.setter
    def ingestion_date(self, op):
        self.__ingestion_date = op

    @property
    def valid_from_date(self):
        return self.__valid_from_date
    @valid_from_date.setter
    def valid_from_date(self, op):
        self.__valid_from_date = op

    @property
    def valid_to_date(self):
        return self.__valid_to_date
    @valid_to_date.setter
    def valid_to_date(self, op):
        self.__valid_to_date = op


    def publish(self):

        return

class PublishableRasterProduct(PublishableProduct):

    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising PublishableRasterProduct')
        super(PublishableRasterProduct, self).__init__()
        self.params = params
        self.vp = vampire_defaults
        self.product_filename = None
        self.summary = None
        self.tags = None
        self.template_file = None
        return

    @property
    def summary(self):
        return self.__summary
    @summary.setter
    def summary(self, op):
        self.__summary = op

    @property
    def tags(self):
        return self.__tags
    @tags.setter
    def tags(self, op):
        self.__tags = op

    @property
    def template_file(self):
        return self.__template_file
    @template_file.setter
    def template_file(self, op):
        self.__template_file = op

    @property
    def product_filename(self):
        return self.__product_filename
    @product_filename.setter
    def product_filename(self, op):
        self.__product_filename = op


class PublishableTabularProduct(PublishableProduct):

    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising PublishableRasterProduct')
        super(PublishableTabularProduct, self).__init__()
        self.params = params
        self.vp = vampire_defaults
        self.database = None
        self.table_name = None
        self.schema = None
        self.product_filename = None
        return

    @property
    def database(self):
        return self.__database
    @database.setter
    def database(self, op):
        self.__database = op

    @property
    def table_name(self):
        return self.__table_name
    @table_name.setter
    def table_name(self, op):
        self.__table_name = op

    @property
    def schema(self):
        return self.__schema
    @schema.setter
    def schema(self, op):
        self.__schema = op

    @property
    def product_filename(self):
        return self.__product_filename
    @product_filename.setter
    def product_filename(self, op):
        self.__product_filename = op




@PublishProductTasksImpl.register_subclass('rainfall_anomaly')
class PublishRainfallAnomalyProduct(PublishableRasterProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        super(PublishRainfallAnomalyProduct, self).__init__(params, vampire_defaults)
        self.product_dir = self.vp.get('CHIRPS_Rainfall_Anomaly', 'output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.summary = '{0} {1}'.format(self.vp.get('CHIRPS_Rainfall_Anomaly', 'default_interval'.capitalize()),
                                        self.vp.get('CHIRPS_Rainfall_Anomaly', 'summary'))
        self.tags = '{0}, {1}'.format(self.vp.get('CHIRPS_Rainfall_Anomaly', 'tags'),
                                      self.vp.get_country_name(self.vp.get('vampire', 'home_country')))
        self.template_file = self.vp.get('CHIRPS_Rainfall_Anomaly', 'template_file')

        self.product_name = 'rainfall_anomaly'
        _product_pattern = self.params['input_pattern']
        _product_files = directory_utils.get_matching_files(self.params['input_dir'], _product_pattern)
        self.product_filename = _product_files[0]
        #        self.product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % self.product_date.strftime('%Y.%m.%d')
        self.publish_name = None
        if 'publish_name' in self.params:
            self.publish_name = self.params['publish_name']
        self.destination_filename = self.product_filename
        # if using geoserver, need to modify destination filename so if can parse the date
        # ie. to have no full stops and be in the format YYYYmmdd
        if self.vp.get('vampire', 'gis_server').lower() == 'geoserver':
            self.destination_filename = os.path.basename(self.product_filename)
            # find date in destination filename and remove full stops
            regex = ''
            new_date = '{0}'.format(self.product_date.strftime('%Y%m%d'))
            if self.vp.get('CHIRPS_Rainfall_Anomaly', 'default_interval').lower() == 'monthly':
                regex = r'\d{4}.\d{2}'
            elif self.vp.get('CHIRPS_Rainfall_Anomaly', 'default_interval').lower() == 'seasonal':
                regex = r'\d{4}.\d{6}'
            elif self.vp.get('CHIRPS_Rainfall_Anomaly', 'default_interval').lower() == 'dekad':
                regex = r'\d{4}.\d{2}.\d{1}'
            self.destination_filename = re.sub(regex, new_date, self.destination_filename)
#        self.destination_filename = 'lka_cli_chirps-v2.0.%s.ratio_anom.tif' % self.product_date.strftime('%Y%m%d')
        self.ingestion_date = self.product_date #- datetime.timedelta(days=int(self.vampire.get('CHIRPS_Rainfall_Anomaly', 'interval')))
        return

@PublishProductTasksImpl.register_subclass('vhi')
class PublishVHIProduct(PublishableRasterProduct):
    """ Initialise PublishVHIProduct object.

    Implementation class for publishing VHI products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        super(PublishVHIProduct, self).__init__(params, vampire_defaults)
        self.product_dir = self.vp.get('MODIS_VHI', 'vhi_product_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.summary = '{0} {1}'.format(self.vp.get('MODIS_VHI', 'interval'.capitalize()),
                                        self.vp.get('MODIS_VHI', 'summary'))
        self.tags = '{0}, {1}'.format(self.vp.get('MODIS_VHI', 'tags'),
                                      self.vp.get_country_name(self.vp.get('vampire', 'home_country')))
        self.template_file = self.vp.get('MODIS_VHI', 'template_file')
        _product_pattern = self.vp.get('MODIS_VHI', 'vhi_pattern')
        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)
        self.product_filename = _product_files[0]
#        self.product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % self.product_date.strftime('%Y.%m.%d')
        self.product_name = self.vp.get('MODIS_VHI', 'product_name')
        self.destination_filename = self.product_filename
        # if using geoserver, need to modify destination filename so if can parse the date
        # ie. to have no full stops and be in the format YYYYmmdd
        if self.vp.get('vampire', 'gis_server').lower() == 'geoserver':
            self.destination_filename = os.path.basename(self.product_filename)
            # find date in destination filename and remove full stops
            regex = ''
            new_date = '{0}'.format(self.product_date.strftime('%Y%m%d'))
            if self.vp.get('MODIS_VHI', 'default_interval').lower() == 'monthly':
                regex = r'\d{4}.\d{2}'
            elif self.vp.get('MODIS_VHI', 'default_interval').lower() == 'seasonal':
                regex = r'\d{4}.\d{6}'
            elif self.vp.get('MODIS_VHI', 'default_interval').lower() == 'dekad':
                regex = r'\d{4}.\d{2}.\d{1}'
            self.destination_filename = re.sub(regex, new_date, self.destination_filename)
        self.ingestion_date = self.product_date #self.valid_from_date
            #self.product_date - datetime.timedelta(days=int(self.vampire.get('MODIS_VHI', 'interval')))
        return

@PublishProductTasksImpl.register_subclass('spi')
class PublishSPIProduct(PublishableRasterProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        super(PublishSPIProduct, self).__init__(params, vampire_defaults)
        self.product_dir = self.vp.get('CHIRPS_SPI', 'output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.summary = '{0} {1}'.format(self.vp.get('CHIRPS_SPI', 'default_interval'.capitalize()),
                                        self.vp.get('CHIRPS_SPI', 'summary'))
        self.tags = '{0}, {1}'.format(self.vp.get('CHIRPS_SPI', 'tags'),
                                      self.vp.get_country(self.vp.get('vampire_tmp', 'home_country')))
        self.template_file = self.vp.get('CHIRPS_SPI', 'template_file')

        _product_pattern = self.params['input_pattern']
        _product_files = directory_utils.get_matching_files(self.params['input_dir'], _product_pattern)
        self.product_filename = _product_files[0]
        #        self.product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % self.product_date.strftime('%Y.%m.%d')
        self.product_name = 'spi'
        self.publish_name = None
        if 'publish_name' in self.params:
            self.publish_name = self.params['publish_name']
#        if self.product_date.day < 11:
#            _dekad = 1
#        elif self.product_date.day < 21:
#            _dekad = 2
#        else:
#            _dekad = 3
#        self.date_string = '{0}.{1}'.format(self.product_date.strftime('%Y.%m'), _dekad)
#        self.product_filename = 'lka_cli_chirps-v2.0.%s.spi.tif' % self.date_string
#        self.product_name = 'spi'

        # if using geoserver, need to modify destination filename so if can parse the date
        # ie. to have no full stops and be in the format YYYYmmdd
        self.destination_filename = self.product_filename
        if self.vp.get('vampire', 'gis_server').lower() == 'geoserver':
            self.destination_filename = os.path.basename(self.product_filename)
            # find date in destination filename and remove full stops
            regex = ''
            new_date = '{0}'.format(self.product_date.strftime('%Y%m%d'))
            if self.vp.get('CHIRPS_SPI', 'default_interval').lower() == 'monthly':
                regex = r'\d{4}.\d{2}'
            elif self.vp.get('CHIRPS_SPI', 'default_interval').lower() == 'seasonal':
                regex = r'\d{4}.\d{6}'
            elif self.vp.get('CHIRPS_SPI', 'default_interval').lower() == 'dekad':
                regex = r'\d{4}.\d{2}.\d{1}'
            self.destination_filename = re.sub(regex, new_date, self.destination_filename)
#        self.destination_filename = 'lka_cli_chirps-v2.0.%s.spi.tif' % self.product_date.strftime('%Y%m%d')
        self.ingestion_date = self.product_date #- datetime.timedelta(days=int(self.vp.get('CHIRPS_SPI', 'interval')))
        return

@PublishProductTasksImpl.register_subclass('vhi_masked')
class PublishMaskedVHIProduct(PublishableRasterProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        super(PublishMaskedVHIProduct, self).__init__(params, vampire_defaults)
        self.product_dir = self.vampire.get('MODIS_VHI', 'vhi_product_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.summary = '{0} {1}'.format(self.vp.get('MODIS_VHI', 'interval'.capitalize()),
                                        self.vp.get('MODIS_VHI', 'summary'))
        self.tags = '{0}, {1}'.format(self.vp.get('MODIS_VHI', 'tags'),
                                      self.vp.get_country_name(self.vp.get('vampire', 'home_country')))
        self.template_file = self.vp.get('MODIS_VHI', 'template_file')
#        self.product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI_cropmask.tif' % self.product_date.strftime('%Y.%m.%d')
        self.product_name = 'vhi_mask'
        _product_pattern = self.params['input_pattern']
        _product_files = directory_utils.get_matching_files(self.params['input_dir'], _product_pattern)
        self.product_filename = _product_files[0]
        #        self.product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % self.product_date.strftime('%Y.%m.%d')
        self.publish_name = None
        if 'publish_name' in self.params:
            self.publish_name = self.params['publish_name']

        # if using geoserver, need to modify destination filename so if can parse the date
        # ie. to have no full stops and be in the format YYYYmmdd
        self.destination_filename = self.product_filename
        if self.vp.get('vampire', 'gis_server').lower() == 'geoserver':
            self.destination_filename = os.path.basename(self.product_filename)
            # find date in destination filename and remove full stops
            regex = ''
            new_date = '{0}'.format(self.product_date.strftime('%Y%m%d'))
            if self.vp.get('MODIS_VHI', 'default_interval').lower() == 'monthly':
                regex = r'\d{4}.\d{2}'
            elif self.vp.get('MODIS_VHI', 'default_interval').lower() == 'seasonal':
                regex = r'\d{4}.\d{6}'
            elif self.vp.get('MODIS_VHI', 'default_interval').lower() == 'dekad':
                regex = r'\d{4}.\d{2}.\d{1}'
            self.destination_filename = re.sub(regex, new_date, self.destination_filename)
#        self.destination_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI_masked.tif' % self.product_date.strftime('%Y%m%d')
        self.ingestion_date = self.product_date #- datetime.timedelta(days=int(self.vampire.get('MODIS_VHI', 'interval')))
        return

@PublishProductTasksImpl.register_subclass('flood_forecast')
class PublishFloodForecastProduct(PublishableRasterProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        super(PublishFloodForecastProduct, self).__init__(params, vampire_defaults)
        self.product_dir = self.vp.get('FLOOD_FORECAST', 'product_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.summary = '{0} {1}'.format(self.vp.get('FLOOD_FORECAST', 'interval'.capitalize()),
                                        self.vp.get('FLOOD_FORECAST', 'summary'))
        self.tags = '{0}, {1}'.format(self.vp.get('FLOOD_FORECAST', 'tags'),
                                      self.vp.get_country_name(self.vp.get('vampire', 'home_country')))
        self.template_file = self.vp.get('FLOOD_FORECAST', 'template_file')
        _product_pattern = self.params['input_pattern']
        # _product_pattern = self.vp.get('FLOOD_FORECAST', 'flood_mosaic_pattern')
        # _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
#        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)
        _product_files = directory_utils.get_matching_files(self.params['input_dir'], _product_pattern)
        self.product_filename = _product_files[0]
#        self.product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % self.product_date.strftime('%Y.%m.%d')

        self.product_name = 'flood_forecast'
        self.publish_name = None
        if 'publish_name' in self.params:
            self.publish_name = self.params['publish_name']
        # if using geoserver, need to modify destination filename so if can parse the date
        # ie. to have no full stops and be in the format YYYYmmdd
        self.destination_filename = re.sub('_fd\d{3}', '', os.path.basename(self.product_filename))
        regex = r'\d{4}.\d{2}.\d{2}'
        new_date = None
        if self.vp.get('vampire', 'gis_server').lower() == 'geoserver':
            # find date in destination filename and remove full stops
            new_date = '{0}'.format(self.product_date.strftime('%Y%m%d'))
        else:
            # find date in destination filename and remove full stops
            new_date = '{0}'.format(self.product_date.strftime('%Y.%m.%d'))
        self.destination_filename = re.sub(regex, new_date, self.destination_filename)

        self.ingestion_date = datetime.datetime.strptime(self.valid_from_date, '%d/%m/%Y')
            #self.product_date - datetime.timedelta(days=int(self.vampire.get('MODIS_VHI', 'interval')))
        return

@PublishProductTasksImpl.register_subclass('days_since_last_rain')
class PublishDSLRProduct(PublishableRasterProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising PublishDSLRProduct task')
        super(PublishDSLRProduct, self).__init__(params, vampire_defaults)
        self.product_dir = self.vp.get('Days_Since_Last_Rain', 'output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.summary = '{0} {1}'.format(self.vp.get('Days_Since_Last_Rain', 'interval'.capitalize()),
                                        self.vp.get('Days_Since_Last_Rain', 'summary'))
        self.tags = '{0}, {1}'.format(self.vp.get('Days_Since_Last_Rain', 'tags'),
                                      self.vp.get_country_name(self.vp.get('vampire', 'home_country')))
        self.template_file = self.vp.get('Days_Since_Last_Rain', 'template_file')
        _product_pattern = self.vp.get('Days_Since_Last_Rain', 'regional_dslr_pattern')
        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)
        self.product_filename = _product_files[0]
#        self.product_filename = 'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI.tif' % self.product_date.strftime('%Y.%m.%d')
        self.product_name = 'days_since_last_rain'
        self.destination_filename = self.product_filename
        # if using geoserver, need to modify destination filename so if can parse the date
        # ie. to have no full stops and be in the format YYYYmmdd
        if self.vp.get('vampire', 'gis_server').lower() == 'geoserver':
            self.destination_filename = os.path.basename(self.product_filename)
            # find date in destination filename and remove full stops
            regex = r'\d{4}.\d{2}.\d{2}'
            new_date = '{0}'.format(self.product_date.strftime('%Y%m%d'))
            self.destination_filename = re.sub(regex, new_date, self.destination_filename)
        self.ingestion_date = self.product_date #datetime.datetime.strptime(self.valid_from_date, '%d/%m/%Y')
            #self.product_date - datetime.timedelta(days=int(self.vampire.get('MODIS_VHI', 'interval')))
        return



@PublishProductTasksImpl.register_subclass('vhi_impact_area')
class PublishVHIAreaImpactProduct(PublishableTabularProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising Area Impact product.')
        super(PublishVHIAreaImpactProduct, self).__init__(params, vampire_defaults)
        self.params = params
        self.vp = vampire_defaults
        self.product_dir = self.vp.get('hazard_impact', 'vhi_output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.database = self.vp.get('database', 'impact_db')
        self.table_name = self.vp.get('database', 'impact_area_table')
        try:
            self.schema = self.vp.get('database', 'impact_area_schema')
        except Exception, e:
            self.schema = self.vp.get('database', 'default_schema')
        _product_pattern = self.vp.get('hazard_impact', 'vhi_area_pattern')
        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)

        self.product_filename = _product_files[0]
        self.product_name = 'vhi_impact_area'
        self.destination_filename = self.product_filename
        self.ingestion_date = self.product_date #self.valid_from_date
        return

@PublishProductTasksImpl.register_subclass('vhi_impact_popn')
class PublishVHIPopnImpactProduct(PublishableTabularProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising Popn Impact product.')
        super(PublishVHIPopnImpactProduct, self).__init__(params, vampire_defaults)
#        self.params = params
#        self.vp = vampire_defaults
        self.product_dir = self.vp.get('hazard_impact', 'vhi_output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.database = self.vp.get('database', 'impact_db')
        self.table_name = self.vp.get('database', 'impact_popn_table')
        try:
            self.schema = self.vp.get('database', 'impact_popn_schema')
        except Exception, e:
            self.schema = self.vp.get('database', 'default_schema')
        _product_pattern = self.vp.get('hazard_impact', 'vhi_popn_pattern')
        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)

        self.product_filename = _product_files[0]
            #'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI_cropmask.tif' % self.product_date.strftime('%Y.%m.%d')
        self.product_name = 'vhi_impact_popn'
        self.destination_filename = self.product_filename
        self.ingestion_date = self.product_date #self.valid_from_date
        return

@PublishProductTasksImpl.register_subclass('flood_impact_area')
class PublishFloodAreaImpactProduct(PublishableTabularProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialize Publish Flood Area Impact product.')
        super(PublishFloodAreaImpactProduct, self).__init__(params, vampire_defaults)
        self.params = params
        self.vp = vampire_defaults
        self.product_dir = self.vp.get('hazard_impact', 'flood_output_dir')
        self.product_date = self.params['start_date'] #datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.database = self.vp.get('database', 'impact_db')
        if 'table' in params:
            self.table_name = params['table']
        else:
            self.table_name = self.vp.get('database', 'flood_impact_area_table')
        try:
            self.schema = self.vp.get('database', 'impact_area_schema')
        except Exception, e:
            self.schema = self.vp.get('database', 'default_schema')
        _product_pattern = self.params['input_pattern'] #self.vp.get('hazard_impact', 'flood_area_pattern')
#        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.params['input_dir'], _product_pattern)

        self.product_filename = _product_files[0]
        self.product_name = 'flood_impact_area'
        self.destination_filename = self.product_filename
        self.ingestion_date = self.product_date #self.valid_from_date
        return

@PublishProductTasksImpl.register_subclass('flood_impact_popn')
class PublishFloodPopnImpactProduct(PublishableTabularProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialize Publish Flood Population Impact product.')
        super(PublishFloodPopnImpactProduct, self).__init__(params, vampire_defaults)
        self.params = params
        self.vp = vampire_defaults
        self.product_dir = self.vp.get('hazard_impact', 'flood_output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.database = self.vp.get('database', 'impact_db')
        if 'table' in params:
            self.table_name = params['table']
        else:
            self.table_name = self.vp.get('database', 'flood_impact_popn_table')
        try:
            self.schema = self.vp.get('database', 'impact_popn_schema')
        except Exception, e:
            self.schema = self.vp.get('database', 'default_schema')
        _product_pattern = self.params['input_pattern'] #self.vp.get('hazard_impact', 'flood_popn_pattern')
#        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)

        self.product_filename = _product_files[0]
        self.product_name = 'flood_impact_popn'
        self.destination_filename = self.product_filename
        self.ingestion_date = self.product_date #self.valid_from_date
        return


@PublishProductTasksImpl.register_subclass('dslr_impact_area')
class PublishDSLRAreaImpactProduct(PublishableTabularProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising Area Impact product.')
        super(PublishDSLRAreaImpactProduct, self).__init__(params, vampire_defaults)
        self.params = params
        self.vp = vampire_defaults
        self.product_dir = self.vp.get('hazard_impact', 'dslr_output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.database = self.vp.get('database', 'impact_db')
        self.table_name = self.vp.get('database', 'dslr_impact_area_table')
        try:
            self.schema = self.vp.get('database', 'dslr_impact_area_schema')
        except Exception, e:
            self.schema = self.vp.get('database', 'default_schema')
        _product_pattern = self.vp.get('hazard_impact', 'dslr_area_pattern')
        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)

        self.product_filename = _product_files[0]
        self.product_name = 'dslr_impact_area'
        self.destination_filename = self.product_filename
        self.ingestion_date = self.product_date #self.valid_from_date
        return

@PublishProductTasksImpl.register_subclass('dslr_impact_popn')
class PublishDSLRPopnImpactProduct(PublishableTabularProduct):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising Popn Impact product.')
        super(PublishDSLRPopnImpactProduct, self).__init__(params, vampire_defaults)
#        self.params = params
#        self.vp = vampire_defaults
        self.product_dir = self.vp.get('hazard_impact', 'dslr_output_dir')
        self.product_date = datetime.datetime.strptime(self.params['start_date'], '%d/%m/%Y')
        self.valid_from_date = self.params['start_date']
        self.valid_to_date = self.params['end_date']
        self.database = self.vp.get('database', 'impact_db')
        self.table_name = self.vp.get('database', 'dslr_impact_popn_table')
        try:
            self.schema = self.vp.get('database', 'impact_popn_schema')
        except Exception, e:
            self.schema = self.vp.get('database', 'default_schema')
        _product_pattern = self.vp.get('hazard_impact', 'dslr_popn_pattern')
        _product_pattern = _product_pattern.replace('(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})', '{0}'.format(self.product_date.strftime('%Y.%m.%d')))
        _product_files = directory_utils.get_matching_files(self.product_dir, _product_pattern)

        self.product_filename = _product_files[0]
            #'lka_phy_MOD13Q1.%s.250m_16_days_EVI_EVI_VCI_VHI_cropmask.tif' % self.product_date.strftime('%Y.%m.%d')
        self.product_name = 'dslr_impact_popn'
        self.destination_filename = self.product_filename
        self.ingestion_date = self.product_date #self.valid_from_date
        return

