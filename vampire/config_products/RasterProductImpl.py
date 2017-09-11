import logging
logger = logging.getLogger(__name__)

class RasterProductImpl(object):
    """ Initialise RasterProductImpl object.

    Abstract implementation class for raster config_products.

    """
    def __init__(self):
        logger.debug('Initialising Raster Product')
        self.valid_from_date = None
        self.valid_to_date = None
        self.product_file = None
        self.product_dir = None
        self.product_pattern = None
        return

    @property
    def product_file(self):
        return self.__product_file
    @product_file.setter
    def product_file(self, of):
        self.__product_file = of

    @property
    def product_dir(self):
        return self.__product_dir
    @product_dir.setter
    def product_dir(self, od):
        self.__product_dir = od

    @property
    def product_pattern(self):
        return self.__product_pattern
    @product_pattern.setter
    def product_pattern(self, op):
        self.__product_pattern = op

    @property
    def valid_from_date(self):
        return self.__valid_from_date
    @valid_from_date.setter
    def valid_from_date(self, sd):
        self.__valid_from_date = sd

    @property
    def valid_to_date(self):
        return self.__valid_to_date
    @valid_to_date.setter
    def valid_to_date(self, ed):
        self.__valid_to_date = ed

    def generate_publish_config(self):
        cfg_string = """
    # Publish product to GIS Server
    - process: Publish
      type: gis_server
      start_date: {start_date}
      end_date: {end_date}""".format(start_date=self.valid_from_date.strftime("%d/%m/%Y"),
                                     end_date=self.valid_to_date.strftime("%d/%m/%Y"))
        if self.product_file is not None:
            cfg_string += """
      input_file: {input_file}""".format(input_file=self.product_file)
        else:
            cfg_string += """
      input_dir: {input_dir}
      input_pattern: '{input_pattern}'
        """.format(input_dir=self.product_dir, input_pattern=self.product_pattern)

        return cfg_string