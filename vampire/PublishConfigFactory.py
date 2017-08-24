import ConfigFactory
import dateutil.rrule
import datetime
import calendar
import os

class PublishConfigFactory(ConfigFactory.ConfigFactory):

    def __init__(self, name, country, start_date, end_date=None):
        ConfigFactory.ConfigFactory.__init__(self, name)
        self.country = country
        self.set_dates(start_date, end_date)
        return

    def set_dates(self, start_date, end_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.year = self.end_date.strftime("%Y")
        self.month = self.end_date.strftime("%m")
        self.day = self.end_date.strftime("%d")
        # self.year = self.start_date.strftime("%Y")
        # self.month = self.start_date.strftime("%m")
        # self.day = self.start_date.strftime("%d")
        _base_date = datetime.datetime.strptime("2000.{0}.01".format(self.month), "%Y.%m.%d")
        self.base_day_of_year = _base_date.timetuple().tm_yday
        self.day_of_year = self.end_date.timetuple().tm_yday
#        self.day_of_year = self.start_date.timetuple().tm_yday
        return

    def _generate_publish_gis_section(self, hazard_file, hazard_dir, hazard_pattern,
                                      start_date, end_date):
        file_string = """
    # Publish data to GIS server
    - process: Publish
      type: gis_server
      start_date: {start_date}
      end_date: {end_date}""".format(start_date=start_date.strftime("%d/%m/%Y"), end_date=end_date.strftime("%d/%m/%Y"))
        if hazard_file is not None:
            file_string += """
      input_file: {input_file}""".format(input_file=hazard_file)
        else:
            file_string += """
      input_dir: {input_dir}
      input_pattern: '{input_pattern}'
        """.format(input_dir=hazard_dir, input_pattern=hazard_pattern)
        return file_string



    def generate_publish_gis(self, product, interval, masked=False):
        _hazard_file = None
        _hazard_dir = None
        _hazard_pattern = None
        filestring = None
        _start_date = self.start_date
        _end_date = self.end_date
        if product == 'vhi':
            if masked:
                _hazard_dir = self.vampire.get('MODIS_VHI', 'vhi_product_dir')
                _hazard_pattern = self.vampire.get('MODIS_VHI', 'vhi_crop_pattern')
            else:
                _hazard_dir = self.vampire.get('MODIS_VHI', 'vhi_product_dir')
                _hazard_pattern = self.vampire.get('MODIS_VHI', 'vhi_pattern')
            _hazard_pattern = _hazard_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
            _hazard_pattern = _hazard_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(self.month))
            _hazard_pattern = _hazard_pattern.replace('(?P<day>\d{2})', '(?P<day>{0})'.format(self.day))
            filestring = self._generate_publish_gis_section(hazard_file=_hazard_file, hazard_dir=_hazard_dir,
                                                            hazard_pattern=_hazard_pattern,

                                                        start_date=_start_date, end_date=_end_date)
        return filestring