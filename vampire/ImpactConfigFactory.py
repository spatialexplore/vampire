import ConfigFactory
import dateutil.rrule
import datetime
import calendar
import os

class ImpactConfigFactory(ConfigFactory.ConfigFactory):

    def __init__(self, name, country, start_date, end_date=None):
        ConfigFactory.ConfigFactory.__init__(self, name)
        self.country = country
        self.set_dates(start_date, end_date)
        return

    def set_dates(self, start_date, end_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.year = self.start_date.strftime("%Y")
        self.month = self.start_date.strftime("%m")
        self.day = self.start_date.strftime("%d")
        _base_date = datetime.datetime.strptime("2000.{0}.01".format(self.month), "%Y.%m.%d")
        self.base_day_of_year = _base_date.timetuple().tm_yday
        self.day_of_year = self.start_date.timetuple().tm_yday

    def _generate_area_impact_section(self, hazard_file, hazard_dir, hazard_pattern,
                                      boundary_file, boundary_dir, boundary_pattern, boundary_field,
                                      output_file, output_dir, output_pattern):
        file_string = """
    # calculate area impact (ha)
    - process: impact
      type: area"""
        if hazard_file is not None:
            file_string += """
      hazard_file: {hazard_file}""".format(hazard_file=hazard_file)
        else:
            file_string += """
      hazard_dir: {hazard_dir}
      hazard_pattern: '{hazard_pattern}'""".format(hazard_dir=hazard_dir, hazard_pattern=hazard_pattern)
        if boundary_file is not None:
            file_string += """
      boundary_file: {boundary_file}""".format(boundary_file=boundary_file)
        else:
            file_string += """
      boundary_dir: {boundary_dir}
      boundary_pattern: '{boundary_pattern}'""".format(boundary_dir=boundary_dir, boundary_pattern=boundary_pattern)
        file_string += """
      boundary_field: {boundary_field}""".format(boundary_field=boundary_field)
        if output_file is not None:
            file_string += """
      output_file: {output_dir}
      """.format(output_dir=output_dir)
        else:
            file_string += """
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'
      """.format(output_dir=output_dir, output_pattern=output_pattern)
        return file_string

    def _generate_popn_impact_section(self, hazard_file, hazard_dir, hazard_pattern,
                                      boundary_file, boundary_dir, boundary_pattern, boundary_field,
                                      population_file,
                                      output_file, output_dir, output_pattern):
        file_string = """
    # calculate population impact (number of people)
    - process: impact
      type: population"""
        if hazard_file is not None:
            file_string += """
      hazard_file: {hazard_file}""".format(hazard_file=hazard_file)
        else:
            file_string += """
      hazard_dir: {hazard_dir}
      hazard_pattern: '{hazard_pattern}'""".format(hazard_dir=hazard_dir, hazard_pattern=hazard_pattern)
        if boundary_file is not None:
            file_string += """
      boundary_file: {boundary_file}""".format(boundary_file=boundary_file)
        else:
            file_string += """
      boundary_dir: {boundary_dir}
      boundary_pattern: '{boundary_pattern}'""".format(boundary_dir=boundary_dir, boundary_pattern=boundary_pattern)

        file_string += """
      boundary_field: {boundary_field}
      population_file: {population_file}""".format(boundary_field=boundary_field, population_file=population_file)

        if output_file is not None:
            file_string += """
      output_file: {output_dir}
      """.format(output_dir=output_dir)
        else:
            file_string += """
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'
        """.format(output_dir=output_dir, output_pattern=output_pattern)
        return file_string

    def generate_impact(self, product, interval):
        _hazard_file = None
        _hazard_dir = None
        _hazard_pattern = None
        _boundary_file = None
        _boundary_pattern = None
        _boundary_dir = None
        _boundary_field = None
        _population_file = None
        _output_file = None
        _output_dir = None
        _output_pattern = None
        filestring = None
        if product == 'vhi':
            _hazard_dir = self.vampire.get('MODIS_VHI', 'vhi_product_dir')
            _hazard_pattern = self.vampire.get('MODIS_VHI', 'vhi_pattern')
            _hazard_pattern = _hazard_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
            _hazard_pattern = _hazard_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(self.month))
            _hazard_pattern = _hazard_pattern.replace('(?P<day>\d{2})', '(?P<day>{0})'.format(self.day))

            _boundary_file = self.vampire.get_country(self.country)['admin_3_boundary']
            _boundary_field = 'dsd_code'

            _output_dir = self.vampire.get('hazard_impact', 'vhi_output_dir')
            _output_pattern = self.vampire.get('hazard_impact', 'vhi_area_output_pattern')

            filestring = self._generate_area_impact_section(hazard_file=_hazard_file, hazard_dir=_hazard_dir,
                                                            hazard_pattern=_hazard_pattern, boundary_file=_boundary_file,
                                                            boundary_dir=_boundary_dir, boundary_pattern=_boundary_pattern,
                                                            boundary_field=_boundary_field, output_file=_output_file,
                                                            output_dir=_output_dir, output_pattern=_output_pattern)
            _population_file = self.vampire.get_country(self.country)['population_layer']
            _output_pattern = self.vampire.get('hazard_impact', 'vhi_popn_output_pattern')
            filestring += self._generate_popn_impact_section(hazard_file=_hazard_file, hazard_dir=_hazard_dir,
                                                            hazard_pattern=_hazard_pattern, boundary_file=_boundary_file,
                                                            boundary_dir=_boundary_dir, boundary_pattern=_boundary_pattern,
                                                            boundary_field=_boundary_field, population_file=_population_file,
                                                            output_file=_output_file,
                                                            output_dir=_output_dir, output_pattern=_output_pattern)

        return filestring