import BaseTaskImpl
import os
import re
import vampire.directory_utils as directory_utils
import vampire.filename_utils as filename_utils
import logging
logger = logging.getLogger(__name__)
try:
    import precipitation_analysis_arc as precipitation_analysis
except ImportError:
    import precipitation_analysis_os as precipitation_analysis

class FloodAlertTaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise FloodAlertTaskImpl object.

    Abstract implementation class for processing flood predictions.

    """
    def __init__(self, params, vampire_defaults):
        super(FloodAlertTaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Flood Alert task')
        return

    def process(self):
        logger.debug("Compute Flood Alert")
        _forecast_file = None
        _forecast_dir = None
        _forecast_pattern = None
        _threshold_file = None
        _threshold_dir = None
        _threshold_pattern = None
        _out_file = None
        _output_dir = None
        _output_pattern = None
        _num_years = None

        if 'forecast_file' in self.params:
            _forecast_file = self.params['forecast_file']
        else:
            if not 'forecast_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No forecast file 'forecast_file' or pattern 'forecast_pattern' specified.", None)
            else:
                if 'forecast_dir' in self.params:
                    _forecast_dir = self.params['forecast_dir']
                else:
                    _forecast_dir = None
                _forecast_pattern = self.params['forecast_pattern']
        if 'threshold_file' in self.params:
            _threshold_file = self.params['threshold_file']
        else:
            if not 'threshold_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No threshold file 'threshold_file' or pattern 'threshold_pattern' specified.", None)
            else:
                if 'threshold_dir' in self.params:
                    _threshold_dir = self.params['threshold_dir']
                else:
                    _threshold_dir = None
                _threshold_pattern = self.params['threshold_pattern']
        if 'output_file' in self.params:
            _out_file = self.params['output_file']
        else:
            if not 'output_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No output file 'output_file' or pattern 'output_pattern' specified.", None)
            else:
                if 'output_dir' in self.params:
                    _output_dir = self.params['output_dir']
                else:
                    _output_dir = None
                _output_pattern = self.params['output_pattern']
        if 'num_years' in self.params:
            _num_years = self.params['num_years']

        self.calc_flood_alert(forecast_filename=_forecast_file, forecast_dir=_forecast_dir,
                              forecast_pattern=_forecast_pattern,
                              threshold_filename=_threshold_file, threshold_dir=_threshold_dir,
                              threshold_pattern=_threshold_pattern,
                              dst_filename=_out_file, dst_dir=_output_dir, dst_pattern=_output_pattern,
                              num_years=_num_years)

    def calc_flood_alert(self, forecast_filename=None, forecast_dir=None, forecast_pattern=None,
                              threshold_filename=None, threshold_dir=None, threshold_pattern=None,
                              dst_filename=None, dst_dir=None, dst_pattern=None, num_years=None):
        logger.info('entering calc_flood_alert')
        if forecast_filename is None:
            # get filenames from pattern and directory
            _forecast_filenames = directory_utils.get_matching_files(forecast_dir, forecast_pattern)
            if _forecast_filenames is None:
                raise ValueError('Cannot find matching forecast files in directory')
        else:
            _forecast_filenames = forecast_filename
        if threshold_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(threshold_dir, threshold_pattern)
            try:
                _threshold_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching flood threshold file in directory')
        else:
            _threshold_filename = threshold_filename
        if dst_dir is not None and not os.path.isdir(dst_dir):
            # destination directory does not exist, create it first
            os.makedirs(dst_dir)
        for f in _forecast_filenames:
            # calculate flood forecast for each file
            if dst_filename is None:
                # TODO this doesn't work for flood alert file names!! Not appropriate

                _dst_pattern = dst_pattern.replace('{num_years}', '{0:0>2}yrs'.format(num_years))
                # get new filename from directory and pattern
                _dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                    os.path.split(f)[1], forecast_pattern, _dst_pattern))
            else:
                _dst_filename = dst_filename
            precipitation_analysis.calc_flood_alert(forecast_filename=f,
                                                    threshold_filename=_threshold_filename,
                                                    dst_filename=_dst_filename
                                                    )
        logger.info('leaving calc_flood_alert')
        return None
