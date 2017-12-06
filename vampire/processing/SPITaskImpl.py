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

class SPITaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(SPITaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Standardised Precipitation Index')
        return

    def process(self):
        logger.debug("Compute standardized precipitation index")
        cur_file = None
        lta_file = None
        ltsd_file = None
        out_file = None
        cur_pattern = None
        lta_pattern = None
        ltsd_pattern = None
        output_pattern = None
        cur_dir = None
        lta_dir = None
        ltsd_dir = None
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

        if 'longterm_sd_file' in self.params:
            ltsd_file = self.params['longterm_sd_file']
        else:
            if not 'longterm_sd_file_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No long term standard deviation file 'longterm_sd_file' or pattern 'longterm_sd_file_pattern' specified.", None)
            else:
                if 'longterm_sd_dir' in self.params:
                    ltsd_dir = self.params['longterm_sd_dir']
                else:
                    ltsd_dir = None
                ltsd_pattern = self.params['longterm_sd_file_pattern']

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

        self.calc_standardized_precipitation_index(cur_filename=cur_file, lta_filename=lta_file,
                                                 ltsd_filename=ltsd_file,
                                                 cur_dir=cur_dir, lta_dir=lta_dir, ltsd_dir=ltsd_dir,
                                                 cur_pattern=cur_pattern, lta_pattern=lta_pattern,
                                                 ltsd_pattern=ltsd_pattern,
                                                 dst_filename=out_file, dst_pattern=output_pattern,
                                                 dst_dir=output_dir )
        return

    def calc_standardized_precipitation_index(self,
                                              dst_filename=None,
                                              cur_filename=None,
                                              lta_filename=None,
                                              ltsd_filename=None,
                                              cur_dir=None,
                                              lta_dir=None,
                                              ltsd_dir=None,
                                              cur_pattern=None,
                                              lta_pattern=None,
                                              ltsd_pattern=None,
                                              dst_pattern=None,
                                              dst_dir=None):

        logger.info('entering calc_standardized_precipitation_index')
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

        if ltsd_filename is None:
            # get filename from pattern and diretory
            files_list = directory_utils.get_matching_files(ltsd_dir, ltsd_pattern)
            try:
                ltsd_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching long-term standard deviation file.')

        if dst_filename is None:
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            # get new filename from directory and pattern
            dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(cur_filename)[1], cur_pattern, dst_pattern))
        precipitation_analysis.calc_standardized_precipitation_index(cur_filename=cur_filename,
                                                                     lta_filename=lta_filename,
                                                                     ltsd_filename=ltsd_filename,
                                                                     dst_filename=dst_filename)
        logger.info('leaving calc_standardized_precipitation_index')
        return None