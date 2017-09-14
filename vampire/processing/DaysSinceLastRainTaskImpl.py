import BaseTaskImpl
import os
import regex
import functools
import datetime
import vampire.directory_utils as directory_utils
import vampire.filename_utils as filename_utils
import logging
logger = logging.getLogger(__name__)
try:
    import precipitation_analysis_arc as precipitation_analysis
except ImportError:
    import precipitation_analysis_os as precipitation_analysis

class DaysSinceLastRainTaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(DaysSinceLastRainTaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Days Since Last Rain task')
        return

    def process(self):
        logger.debug("Compute Days Since Last Rain")
        if 'input_dir' in self.params:
            _input_dir = self.params['input_dir']
        else:
            _input_dir = None
        if 'output_dir' in self.params:
            _output_dir = self.params['output_dir']
        else:
            _output_dir = None
        if 'file_pattern' in self.params:
            _file_pattern = self.params['file_pattern']
        else:
            _file_pattern = None
        if 'threshold' in self.params:
            _threshold = self.params['threshold']
        else:
            _threshold = None
        if 'max_days' in self.params:
            _max_days = self.params['max_days']
        else:
            _max_days = None
        if 'start_date' in self.params:
            _start_date = self.params['start_date']
        else:
            _start_date = None
        self.calc_days_since_last_rainfall(data_dir=_input_dir, data_pattern=_file_pattern,
                                         dst_dir=_output_dir, start_date=_start_date,
                                         threshold=_threshold, max_days=_max_days)

    def calc_days_since_last_rainfall(self, data_dir, data_pattern, dst_dir, start_date, threshold, max_days):
        logger.info('entering calc_days_since_last_rainfall')
        # get list of files from start_date back max_days
        files_list = directory_utils.get_matching_files(data_dir, data_pattern)
        raster_list = []
        _r_in = regex.compile(data_pattern)
        for f in files_list:
            _m = _r_in.match(os.path.basename(f))
            max_date = start_date - datetime.timedelta(days=max_days)
            f_date = datetime.date(int(_m.group('year')), int(_m.group('month')), int(_m.group('day')))
            if max_date <= f_date <= start_date:
                raster_list.append(f)

        def replace_closure(subgroup, replacement, m):
            if m.group(subgroup) not in [None, '']:
                start = m.start(subgroup)
                end = m.end(subgroup)
                return m.group()[:start] + replacement + m.group()[end:]

        _ref_file = regex.sub(data_pattern, functools.partial(replace_closure, 'year', '{0}'.format(start_date.year)),
                           os.path.basename(files_list[0]))
        _ref_file = regex.sub(data_pattern, functools.partial(replace_closure, 'month', '{0:0>2}'.format(start_date.month)),
                           _ref_file)
        _ref_file = regex.sub(data_pattern, functools.partial(replace_closure, 'day', '{0:0>2}'.format(start_date.day)),
                           _ref_file)
        dslw_file = os.path.join(dst_dir,
                                 filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                         self.vp.get(
                                                                             'CHIRPS_Days_Since_Last_Rain',
                                                                             'regional_dslr_output_pattern')))
        dsld_file = os.path.join(dst_dir,
                                 filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                         self.vp.get(
                                                                             'CHIRPS_Days_Since_Last_Rain',
                                                                             'regional_dsld_output_pattern')))
        num_wet_file = os.path.join(dst_dir,
                                    filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                            self.vp.get(
                                                                                'CHIRPS_Days_Since_Last_Rain',
                                                                                'regional_wet_accum_output_pattern')))
        ra_file = os.path.join(dst_dir,
                               filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                       self.vp.get(
                                                                            'CHIRPS_Days_Since_Last_Rain',
                                                                           'regional_accum_output_pattern')))
        _temp_dir = self.vp.get('directories', 'temp_dir')
        if not os.path.exists(_temp_dir):
            os.makedirs(_temp_dir)
        precipitation_analysis.days_since_last_rain(raster_list=raster_list,
                                                    dslw_filename=dslw_file,
                                                    dsld_filename=dsld_file,
                                                    num_wet_days_filename=num_wet_file,
                                                    rainfall_accum_filename=ra_file,
                                                    temp_dir=_temp_dir,
                                                    threshold=threshold, max_days=max_days)
        logger.info('leaving calc_days_since_last_rainfall')
        return None
