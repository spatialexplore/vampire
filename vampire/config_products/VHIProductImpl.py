import logging
import os
import BaseProduct
import RasterDatasetImpl
import RasterProductImpl

logger = logging.getLogger(__name__)

class VHIProductImpl(RasterProductImpl.RasterProductImpl):
    """ Initialise VHIProductImpl.

    Implementation class for VHIProduct.
    Initialise object parameters.

    Parameters
    ----------
    country : string
        Region of dataset - country name or 'global'.
    product_date : datetime
        Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
        the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
        the product_date refers to the start of the season (3 month period).
    interval : string
        Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
    vampire_defaults : object
        VAMPIREDefaults object containing VAMPIRE system default values.

    """
    def __init__(self, country, product_date, interval, vampire_defaults):
        super(VHIProductImpl, self).__init__()
        self.product_name = 'vhi'
        self.country = country
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        self.product = self.vp.get('MODIS', 'vegetation_product')
        self.day_of_year = self.product_date.timetuple().tm_yday

        self.vci_product = BaseProduct.BaseProduct.create(product_type='vci', interval=self.interval,
                                                          product_date=self.product_date,
                                                          vampire_defaults=self.vp, country=self.country)
        self.tci_product = BaseProduct.BaseProduct.create(product_type='tci', interval=self.interval,
                                                          product_date=self.product_date,
                                                          vampire_defaults=self.vp, country=self.country)
        self.valid_from_date = self.vci_product.valid_from_date
        self.valid_to_date = self.vci_product.valid_to_date
        return


    def generate_header(self):
        return ''

    """ Generate a config file process for the vegetation condition index (VCI) product.

    Generate VAMPIRE config file processes for the product including download and crop if specified.

    Parameters
    ----------
    output_dir : string
        Path for product output. If the output_dir is None, the VAMPIRE default SPI product directory
        will be used.
    cur_file : string
        Path for current precipitation file. Default is None. If None, cur_dir and cur_pattern will be used to find
        the file.
    cur_dir : string
        Directory path for current precipitation file. Default is None. If cur_file is set, cur_dir is not used.
    cur_pattern : string
        Regular expression pattern for finding current precipitation file. Default is None. If cur_file is set,
        cur_pattern is not used.
    lta_file : string
        Path for long-term average precipitation file. Default is None. If None, lta_dir and lta_pattern will be
        used to find the file.
    lta_dir : string
        Directory path for long-term average precipitation file. Default is None. If lta_file is set, lta_dir is not
        used.
    lta_pattern : string
        Regular expression pattern for finding long-term average precipitation file. Default is None. If lta_file is
        set, lta_pattern is not used.
    output_file : string
        Directory path for output rainfall anomaly file. Default is None. If output_file is set, output_dir is not used.
    output_pattern : string
        Pattern for specifying output filename. Used in conjuction with cur_pattern. Default is None. If output_file is
        set, output_pattern is not used.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def generate_config(self, tci_file=None, tci_dir=None, tci_pattern=None,
                        vci_file=None, vci_dir=None, vci_pattern=None,
                        output_file=None, output_dir=None, output_pattern=None,
                        reproject='TCI'):
        config = """
    ## Processing chain begin - Compute Vegetation Health Index\n"""
        config += self.vci_product.generate_config()
        config += self.tci_product.generate_config()
        if tci_file is None:
            if tci_dir is None:
                _tci_dir = self.vp.get('MODIS_TCI', 'tci_product_dir')
            else:
                _tci_dir = tci_dir
            _tci_file = None
            if tci_pattern is None:
                _tci_pattern = self.vp.get('MODIS_TCI', 'tci_pattern')
                _tci_pattern = _tci_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
                _tci_pattern = _tci_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
                _tci_pattern = _tci_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
            else:
                _tci_pattern = tci_pattern
        else:
            _tci_file = tci_file
            _tci_pattern = None
            _tci_dir = None

        if vci_file is None:
            if vci_dir is None:
                _vci_dir = self.vp.get('MODIS_VCI', 'vci_product_dir')
            else:
                _vci_dir = vci_dir
            _vci_file = None
            if vci_pattern is None:
                _vci_pattern = self.vp.get('MODIS_VCI', 'vci_pattern')
                _vci_pattern = _vci_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
                _vci_pattern = _vci_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
                _vci_pattern = _vci_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
            else:
                _vci_pattern = vci_pattern
        else:
            _vci_file = vci_file
            _vci_pattern = None
            _vci_dir = None

        _output_pattern = None
        if output_file is None:
            if output_dir is None:
                self.product_dir = self.vp.get('MODIS_VHI', 'vhi_product_dir')
            else:
                self.product_dir = output_dir
            if output_pattern is None:
                _output_pattern = self.vp.get('MODIS_VHI', 'vhi_output_pattern')
            else:
                _output_pattern = output_pattern
            self.product_file = None
        else:
            self.product_file = output_file

        if reproject is not None:
            if reproject == 'TCI':
                _tci_resample_pattern = self.vp.get('MODIS_TCI', 'tci_output_pattern')
                _tci_resample_pattern = _tci_resample_pattern.replace('.TCI', '.TCI_resample')
                config += self.generate_match_projection_section(master_dir=_vci_dir,
                                                                 slave_dir=_tci_dir,
                                                                 output_dir=_tci_dir,
                                                                 master_pattern=_vci_pattern,
                                                                 slave_pattern=_tci_pattern,
                                                                 output_pattern=_tci_resample_pattern)
                _tci_pattern = _tci_pattern.replace('.TCI', '.TCI_resample')
            elif reproject == 'VCI':
                _vci_resample_pattern = self.vp.get('MODIS_VCI', 'vci_output_pattern')
                _vci_resample_pattern = _vci_resample_pattern.replace('.VCI', '.VCI_resample')
                config += self.generate_match_projection_section(master_dir=_tci_dir,
                                                                 slave_dir=_vci_dir,
                                                                 output_dir=_vci_dir,
                                                                 master_pattern=_tci_pattern,
                                                                 slave_pattern=_vci_pattern,
                                                                 output_pattern=_vci_resample_pattern)
                _vci_pattern = _vci_pattern.replace('.VCI', '.VCI_resample')

        config += self.generate_vhi_section(tci_file=_tci_file, tci_dir=_tci_dir, tci_pattern=_tci_pattern,
                                            vci_file=_vci_file, vci_dir=_vci_dir, vci_pattern=_vci_pattern,
                                            output_file=self.product_file, output_dir=self.product_dir,
                                            output_pattern=_output_pattern)
        # TODO: what if output_pattern is specified?
        self.product_pattern = self.vp.get('MODIS_VHI', 'vhi_pattern')
        self.product_pattern = self.product_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
        self.product_pattern = self.product_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
        self.product_pattern = self.product_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))

        return config

    def generate_mask_config(self, boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None):
        config = """
    ## Processing chain begin - Mask VHI\n"""

        if self.product_file is None:
            if self.product_dir is None:
                self.product_dir = self.vp.get('MODIS_VHI', 'vhi_product_dir')
            self.product_pattern = self.vp.get('MODIS_VHI', 'vhi_pattern')
            self.product_pattern = self.product_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
            self.product_pattern = self.product_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
            self.product_pattern = self.product_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))

        _output_dir = None
        _output_pattern = None
        if output_file is None:
            if output_dir is None:
                _output_dir = self.vp.get('MODIS_VHI', 'vhi_product_dir')
            else:
                _output_dir = output_dir
            if output_pattern is None:
                _output_pattern = self.vp.get('MODIS_VHI', 'vhi_crop_output_pattern')
            else:
                _output_pattern = output_pattern
            _output_file = None
        else:
            _output_file = output_file

        _boundary_dir = None
        _boundary_pattern = None
        if boundary_file is None:
            _boundary_file = self.vp.get_country(self.country)['crop_boundary']
        else:
            _boundary_file = boundary_file
        _raster = RasterDatasetImpl.RasterDatasetImpl()
        config += _raster.generate_mask_section(input_file=self.product_file, input_dir=self.product_dir,
                                                input_pattern=self.product_pattern,
                                                output_file=_output_file, output_dir=_output_dir,
                                                output_pattern=_output_pattern, boundary_file=_boundary_file,
                                                no_data=False)
        self.product_dir = _output_dir
        self.product_pattern = self.vp.get('MODIS_VHI', 'vhi_crop_pattern')
        self.product_pattern = self.product_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
        self.product_pattern = self.product_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
        self.product_pattern = self.product_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
        return config


    def generate_vhi_section(self, tci_file, tci_dir, tci_pattern,
                             vci_file, vci_dir, vci_pattern,
                             output_file, output_dir, output_pattern):
        config = """
    # Compute vegetation health index
    - process: Analysis
      type: VHI"""
        if vci_file is not None:
            config += """
      VCI_file: {vci_file}""".format(vci_file=vci_file)
        else:
            config += """
      VCI_dir: {vci_dir}
      VCI_pattern: '{vci_pattern}'""".format(vci_dir=vci_dir, vci_pattern=vci_pattern)

        if tci_file is not None:
            config += """
      TCI_file: {tci_file}""".format(tci_file=tci_file)
        else:
            config += """
      TCI_dir: {tci_dir}
      TCI_pattern: '{tci_pattern}'""".format(tci_dir=tci_dir, tci_pattern=tci_pattern)

        if output_file is not None:
            config += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            config += """
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'""".format(output_dir=output_dir, output_pattern=output_pattern)

        return config

    def generate_match_projection_section(self, master_dir, slave_dir, output_dir,
                                          master_pattern, slave_pattern, output_pattern):
        file_string = """
    - process: Raster
      type: match_projection
      master_dir: {master_dir}
      master_pattern: '{master_pattern}'
      slave_dir: {slave_dir}
      slave_pattern: '{slave_pattern}'
      output_dir: {output_dir}
      output_pattern:  '{output_pattern}'
    """.format(master_dir=master_dir, master_pattern=master_pattern, slave_dir=slave_dir,
                   slave_pattern=slave_pattern, output_dir=output_dir, output_pattern=output_pattern)
        return file_string
