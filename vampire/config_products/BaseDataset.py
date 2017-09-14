import CHIRPSDatasetImpl
import MODISEVIDatasetImpl
import MODISLSTDatasetImpl
import GlobalForecastSystemDatasetImpl
import logging
logger = logging.getLogger(__name__)

class BaseDataset():
    subclasses = {}

    @classmethod
    def register_subclass(cls, dataset_type):
        def decorator(subclass):
            cls.subclasses[dataset_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, dataset_type, interval, product_date, vampire_defaults, region=None):
        if dataset_type not in cls.subclasses:
            logger.debug('Bad dataset type {}'.format(dataset_type))
            raise ValueError('Bad dataset type {}'.format(dataset_type))

        return cls.subclasses[dataset_type](interval, product_date, vampire_defaults, region)

@BaseDataset.register_subclass('CHIRPS')
class CHIRPSDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        self.impl = CHIRPSDatasetImpl.CHIRPSDatasetImpl(interval, product_date, vampire_defaults, region)
        return

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, data_dir=None, download=True, crop=True, crop_dir=None):
        return self.impl.generate_config(data_dir, download, crop, crop_dir)

    def start_date(self):
        return self.impl.start_date
    def set_start_date(self, sd):
        self.impl.start_date = sd
    def end_date(self):
        return self.impl.end_date
    def set_end_date(self, sd):
        self.impl.end_date = sd

@BaseDataset.register_subclass('MODIS_EVI')
class MODISEVIDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        self.impl = MODISEVIDatasetImpl.MODISEVIDatasetImpl(interval, product_date, vampire_defaults, region)
        return

    def start_date(self):
        return self.impl.start_date
    def set_start_date(self, sd):
        self.impl.start_date = sd

    def end_date(self):
        return self.impl.end_date
    def set_end_date(self, sd):
        self.impl.end_date = sd


    def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, extract_dir=None,
                        crop=True, crop_dir=None):
        return self.impl.generate_config(data_dir=data_dir, download=download, mosaic_dir=mosaic_dir,
                                         tiles=tiles, extract_dir=extract_dir, crop=crop, crop_dir=crop_dir)

@BaseDataset.register_subclass('MODIS_LST')
class MODISLSTDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        self.impl = MODISLSTDatasetImpl.MODISLSTDatasetImpl(interval, product_date, vampire_defaults, region)
        return


    def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, extract_dir=None,
                        crop=True, crop_dir=None):
        return self.impl.generate_config(data_dir=data_dir, download=download, mosaic_dir=mosaic_dir,
                                         tiles=tiles, crop=crop, crop_dir=crop_dir)
    @property
    def product(self):
        return self.impl.product

    @product.setter
    def product(self, product):
        self.impl.product = product

    def start_date(self):
        return self.impl.start_date
    def set_start_date(self, start_date):
        self.impl.start_date = start_date

    def end_date(self):
        return self.impl.end_date
    def set_end_date(self, end_date):
        self.impl.end_date = end_date


@BaseDataset.register_subclass('GFS')
class GlobalForecastSystemDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        self.impl = GlobalForecastSystemDatasetImpl.GlobalForecastSystemDatasetImpl(interval, product_date, vampire_defaults, region)
        return

    def start_date(self):
        return self.impl.start_date
    def set_start_date(self, sd):
        self.impl.start_date = sd
    def end_date(self):
        return self.impl.end_date
    def set_end_date(self, sd):
        self.impl.end_date = sd


    def generate_config(self, data_dir=None, variable=None, level=None, forecast_hr=None, download=True,
                        crop=True, crop_dir=None):
        return self.impl.generate_config(data_dir=data_dir, variable=variable, level=level, forecast_hr=forecast_hr,
                                         download=download, crop=crop, crop_dir=crop_dir)
