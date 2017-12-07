import logging
import os

import BaseTaskImpl
import directory_utils as directory_utils
import filename_utils as filename_utils

logger = logging.getLogger(__name__)
try:
    import precipitation_analysis_arc as precipitation_analysis
except ImportError:
    import precipitation_analysis_os as precipitation_analysis

class RainfallAnomalyTaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(RainfallAnomalyTaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Rainfall Anomaly')
        return

    def process(self):
        logger.debug("Compute monthly rainfall anomaly")
        cur_file = None
        lta_file = None
        out_file = None
        cur_pattern = None
        lta_pattern = None
        output_pattern = None
        cur_dir = None
        lta_dir = None
        output_dir = None
        if 'current_file' in self.params:
            cur_file = self.params['current_file']
        else:
            if not 'current_file_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No current file 'current_file' or pattern 'current_file_pattern' specified.", None)
            else:
                if 'current_dir' in self.params:
                    cur_dir = self.params['current_dir']
                else:
                    cur_dir = None

                cur_pattern = self.params['current_file_pattern']

        # try:
        #     cur_file = process['current_file']
        # except Exception, e:
        #     raise ConfigFileError("No current file 'current_file' specified.", e)
        if 'longterm_avg_file' in self.params:
            lta_file = self.params['longterm_avg_file']
        else:
            if not 'longterm_avg_file_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No long term average file 'longterm_avg_file' or pattern 'longterm_avg_file_pattern' specified.", None)
            else:
                if 'longterm_avg_dir' in self.params:
                    lta_dir = self.params['longterm_avg_dir']
                else:
                    lta_dir = None
                lta_pattern = self.params['longterm_avg_file_pattern']
#            try:
#                lta_file = process['longterm_avg_file']
#            except Exception, e:
#                raise ConfigFileError("No long term average file 'longterm_avg_file' specified.", e)
        if 'output_file' in self.params:
            out_file = self.params['output_file']
        else:
            if not 'output_file_pattern':
                raise  BaseTaskImpl.ConfigFileError("No output file 'output_file' or output pattern 'output_file_pattern' specified.", None)
            else:
                if 'output_dir' in self.params:
                    output_dir = self.params['output_dir']
                else:
                    output_dir = None
                output_pattern = self.params['output_file_pattern']
#            try:
#                out_file = process['output_file']
#            except Exception, e:
#                raise ConfigFileError("No output file 'output_file' specified.", e)

        self.calc_rainfall_anomaly(cur_filename=cur_file, lta_filename=lta_file,
                                 cur_dir=cur_dir, lta_dir=lta_dir,
                                 cur_pattern=cur_pattern, lta_pattern=lta_pattern,
                                 dst_filename=out_file, dst_pattern=output_pattern, dst_dir=output_dir )

    # Calculate rainfall anomaly given a precipitation file, long-term average and output result to file.
    # Precipitation file can be given specifically, or as a pattern and directory to search in.
    # Long-term average file can be given specifically, of as a pattern and directory to search in.
    # Destination file can be given specifically, of a filename can be generated based on a pattern with parameters
    # from the precipitation file, and saved in the directory specified.
    # Actual calculation of rainfall anomaly is carried out in the calc_rainfall_anomaly function appropriate to the
    # system (i.e. ArcPy or opensource)
    def calc_rainfall_anomaly(self, dst_filename=None, cur_filename=None, lta_filename=None,
                              cur_dir=None, lta_dir=None,
                              cur_pattern=None, lta_pattern=None, dst_pattern=None,
                              dst_dir=None
                             ):
        logger.info('entering calc_rainfall_anomaly')
        if cur_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(cur_dir, cur_pattern)
            try:
                cur_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching rainfall file in directory')
        if lta_filename is None:
            # get filename from pattern and diretory
            files_list = directory_utils.get_matching_files(lta_dir, lta_pattern)
            try:
                lta_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching long-term average file.')

        if dst_filename is None:
            # get new filename from directory and pattern
            dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(cur_filename)[1], cur_pattern, dst_pattern))
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        precipitation_analysis.calc_rainfall_anomaly(cur_filename=cur_filename,
                                                     lta_filename=lta_filename,
                                                     dst_filename=dst_filename)
        logger.info('leaving calc_rainfall_anomaly')
        return None
