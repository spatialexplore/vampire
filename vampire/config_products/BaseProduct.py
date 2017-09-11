import VampireDefaults
import RainfallAnomalyProductImpl
import SPIProductImpl
import VCIProductImpl
import TCIProductImpl
import VHIProductImpl
import MODISEVILongtermAverageProductImpl
import MODISLSTLongtermAverageProductImpl
import CHIRPSLongtermAverageProductImpl
import DaysSinceLastRainProductImpl
import logging
logger = logging.getLogger(__name__)

class BaseProduct():
    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, product_type, country, product_date, interval, vampire_defaults=None):
        if product_type not in cls.subclasses:
            raise ValueError('Bad product type {}'.format(product_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[product_type](country, product_date, interval, vp)

@BaseProduct.register_subclass('vci')
class VCIProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = VCIProductImpl.VCIProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def product_file(self):
        return self.impl.product_file
    @property
    def product_dir(self):
        return self.impl.product_dir
    @property
    def product_pattern(self):
        return self.impl.product_pattern
    @property
    def valid_from_date(self):
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        return self.impl.valid_to_date

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, evi_cur_file=None, evi_cur_dir=None, evi_cur_pattern=None,
                        evi_max_file=None, evi_max_dir=None, evi_max_pattern=None,
                        evi_min_file=None, evi_min_dir=None, evi_min_pattern=None,
                        output_filename=None, output_dir=None, output_pattern=None):
        return self.impl.generate_config(evi_cur_file, evi_cur_dir, evi_cur_pattern, evi_max_file, evi_max_dir,
                                         evi_max_pattern, evi_min_file, evi_min_dir, evi_min_pattern, output_filename,
                                         output_dir, output_pattern)

@BaseProduct.register_subclass('tci')
class TCIProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = TCIProductImpl.TCIProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def product_file(self):
        return self.impl.product_file
    @property
    def product_dir(self):
        return self.impl.product_dir
    @property
    def product_pattern(self):
        return self.impl.product_pattern
    @property
    def valid_from_date(self):
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        return self.impl.valid_to_date

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, lst_cur_file=None, lst_cur_dir=None, lst_cur_pattern=None,
                        lst_max_file=None, lst_max_dir=None, lst_max_pattern=None,
                        lst_min_file=None, lst_min_dir=None, lst_min_pattern=None,
                        output_filename=None, output_dir=None, output_pattern=None):
        return self.impl.generate_config(lst_cur_file, lst_cur_dir, lst_cur_pattern, lst_max_file, lst_max_dir,
                                         lst_max_pattern, lst_min_file, lst_min_dir, lst_min_pattern, output_filename,
                                         output_dir, output_pattern)

@BaseProduct.register_subclass('vhi')
class VHIProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = VHIProductImpl.VHIProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def product_file(self):
        return self.impl.product_file
    @property
    def product_dir(self):
        return self.impl.product_dir
    @property
    def product_pattern(self):
        return self.impl.product_pattern
    @property
    def valid_from_date(self):
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        return self.impl.valid_to_date

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, tci_file=None, tci_dir=None, tci_pattern=None,
                        vci_file=None, vci_dir=None, vci_pattern=None,
                        output_file=None, output_dir=None, output_pattern=None,
                        reproject='TCI'):
        return self.impl.generate_config(tci_file, tci_dir, tci_pattern, vci_file, vci_dir, vci_pattern,
                                         output_file, output_dir, output_pattern, reproject)

    def generate_mask_config(self, boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None):
        return self.impl.generate_mask_config(boundary_file=boundary_file, boundary_dir=boundary_dir,
                                              boundary_pattern=boundary_pattern, boundary_field=boundary_field,
                                              output_file=output_file, output_dir=output_dir,
                                              output_pattern=output_pattern)

    def generate_publish_config(self):
        return self.impl.generate_publish_config()

@BaseProduct.register_subclass('rainfall_anomaly')
class RainfallAnomalyProduct(BaseProduct):
  # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = RainfallAnomalyProductImpl.RainfallAnomalyProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        return self.impl.generate_header()


    def generate_config(self, output_dir=None, cur_file=None, cur_dir=None, cur_pattern=None,
                        lta_file=None, lta_dir=None, lta_pattern=None, output_file=None,
                        output_pattern=None):
        return self.impl.generate_config(output_dir, cur_file, cur_dir, cur_pattern,
                        lta_file, lta_dir, lta_pattern, output_file,
                        output_pattern)

@BaseProduct.register_subclass('spi')
class SPIProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = SPIProductImpl.SPIProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, output_dir=None, cur_file=None, cur_dir=None, cur_pattern=None,
                        lta_file=None, lta_dir=None, lta_pattern=None, ltsd_file=None, ltsd_dir=None,
                        ltsd_pattern=None, output_file=None, output_pattern=None):
        return self.impl.generate_config(output_dir, cur_file, cur_dir, cur_pattern,
                        lta_file, lta_dir, lta_pattern, ltsd_file, ltsd_dir, ltsd_pattern,
                        output_file, output_pattern)

@BaseProduct.register_subclass('evi_longterm_average')
class MODISEVILongtermAverageProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = MODISEVILongtermAverageProductImpl.MODISEVILongtermAverageProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        return self.impl.generate_config(input_dir=input_dir, output_dir=output_dir, input_pattern=input_pattern,
                        output_pattern=output_pattern, functions=functions, download=download)


@BaseProduct.register_subclass('lst_longterm_average')
class MODISLSTLongtermAverageProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = MODISLSTLongtermAverageProductImpl.MODISLSTLongtermAverageProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        return self.impl.generate_config(input_dir=input_dir, output_dir=output_dir, input_pattern=input_pattern,
                        output_pattern=output_pattern, functions=functions, download=download)


@BaseProduct.register_subclass('chirps_longterm_average')
class CHIRPSLongtermAverageProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = CHIRPSLongtermAverageProductImpl.CHIRPSLongtermAverageProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        return self.impl.generate_config(input_dir=input_dir, output_dir=output_dir, input_pattern=input_pattern,
                        output_pattern=output_pattern, functions=functions, download=download)

@BaseProduct.register_subclass('days_since_last_rain')
class DaysSinceLastRainProduct(BaseProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = DaysSinceLastRainProductImpl.DaysSinceLastRainProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, data_dir=None, output_dir=None, file_pattern=None,
                        threshold=None, max_days=None, download=True, crop=True, crop_dir=None):
        return self.impl.generate_config(data_dir=data_dir, output_dir=output_dir, file_pattern=file_pattern,
                                         threshold=threshold, max_days=max_days, download=download,
                                         crop=crop, crop_dir=crop_dir)



