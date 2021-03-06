import logging
import datetime
logger = logging.getLogger(__name__)

class ImpactProductImpl(object):
    """ Initialise ImpactProductImpl object.

    Abstract implementation class for impact config_products.

    """
    def __init__(self):
        logger.debug('Initialising Impact Product')
        self.product_name = None
        self.valid_from_date = None
        self.valid_to_date = None
        self.output_file = None
        self.output_dir = None
        self.output_pattern = None
        self.publish_pattern = None
        return

    @property
    def output_file(self):
        return self.__output_file
    @output_file.setter
    def output_file(self, of):
        self.__output_file = of

    @property
    def product_name(self):
        return self.__product_name
    @product_name.setter
    def product_name(self, pn):
        self.__product_name = pn

    @property
    def output_dir(self):
        return self.__output_dir
    @output_dir.setter
    def output_dir(self, od):
        self.__output_dir = od

    @property
    def output_pattern(self):
        return self.__output_pattern
    @output_pattern.setter
    def output_pattern(self, op):
        self.__output_pattern = op

    @property
    def publish_pattern(self):
        return self.__publish_pattern
    @publish_pattern.setter
    def publish_pattern(self, op):
        self.__publish_pattern = op

    @property
    def valid_from_date(self):
        if type(self.__valid_from_date) != datetime.datetime:
            return self.__valid_from_date()
        return self.__valid_from_date
    @valid_from_date.setter
    def valid_from_date(self, sd):
        self.__valid_from_date = sd

    @property
    def valid_to_date(self):
        if type(self.__valid_to_date) != datetime.datetime:
            return self.__valid_to_date()
        return self.__valid_to_date
    @valid_to_date.setter
    def valid_to_date(self, ed):
        self.__valid_to_date = ed

    def generate_publish_config(self):
        cfg_string = """
    # Publish product to Database
    - process: Publish
      type: database
      product: {product}
      start_date: {start_date}
      end_date: {end_date}""".format(product=self.product_name, start_date=self.valid_from_date.strftime("%Y-%m-%d"),
                                     end_date=self.valid_to_date.strftime("%Y-%m-%d"))
        if self.output_file is not None:
            cfg_string += """
      input_file: {input_file}""".format(input_file=self.output_file)
        else:
            cfg_string += """
      input_dir: {input_dir}
      input_pattern: '{input_pattern}'
        """.format(input_dir=self.output_dir, input_pattern=self.publish_pattern)

        return cfg_string