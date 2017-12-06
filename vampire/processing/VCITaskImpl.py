import logging
import os

import BaseTaskImpl
import directory_utils as directory_utils
import filename_utils as filename_utils

logger = logging.getLogger(__name__)
try:
    import vegetation_analysis_arc as vegetation_analysis
except ImportError:
    import vegetation_analysis_os as vegetation_analysis

class VCITaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(VCITaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Rainfall Anomaly')
        return

    def process(self):
        _cur_file = None
        _cur_dir = None
        _cur_pattern = None
        _evi_max_file = None
        _evi_min_file = None
        _evi_max_dir = None
        _evi_min_dir = None
        _evi_max_pattern = None
        _evi_min_pattern = None
        _output_file = None
        _output_dir = None
        _output_pattern = None

        logger.debug("Compute Vegetation Condition Index")
        if 'current_file' in self.params:
            _cur_file = self.params['current_file']
        else:
            if not 'current_file_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No current file 'current_file' or pattern 'current_file_pattern' specified.", None)
            else:
                if 'current_dir' in self.params:
                    _cur_dir = self.params['current_dir']
                else:
                    _cur_dir = None

                _cur_pattern = self.params['current_file_pattern']
        if 'EVI_max_file' in self.params:
            _evi_max_file = self.params['EVI_max_file']
        else:
            if not 'EVI_max_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No EVI long-term maximum file 'EVI_max_file' or pattern 'EVI_max_pattern' specified.", None)
            else:
                if 'EVI_max_dir' in self.params:
                    _evi_max_dir = self.params['EVI_max_dir']
                else:
                    _evi_max_dir = None
                _evi_max_pattern = self.params['EVI_max_pattern']

        if 'EVI_min_file' in self.params:
            _evi_min_file = self.params['EVI_min_file']
        else:
            if not 'EVI_min_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No EVI long-term minimum file 'EVI_min_file' or pattern 'EVI_min_pattern' specified.", None)
            else:
                if 'EVI_min_dir' in self.params:
                    _evi_min_dir = self.params['EVI_min_dir']
                else:
                    _evi_min_dir = None
                _evi_min_pattern = self.params['EVI_min_pattern']
        if 'output_file' in self.params:
            _output_file = self.params['output_file']
        else:
            if not 'output_file_pattern':
                raise  BaseTaskImpl.ConfigFileError("No output file 'output_file' or output pattern 'output_file_pattern' specified.", None)
            else:
                if 'output_dir' in self.params:
                    _output_dir = self.params['output_dir']
                else:
                    _output_dir = None
                _output_pattern = self.params['output_file_pattern']
        self.calc_vci(cur_filename=_cur_file, cur_dir=_cur_dir, cur_pattern=_cur_pattern,
                    evi_max_filename=_evi_max_file, evi_max_dir=_evi_max_dir, evi_max_pattern=_evi_max_pattern,
                    evi_min_filename=_evi_min_file, evi_min_dir=_evi_min_dir, evi_min_pattern=_evi_min_pattern,
                    dst_filename=_output_file, dst_dir=_output_dir, dst_pattern=_output_pattern)

    def calc_vci(self, cur_filename=None, cur_dir=None, cur_pattern=None,
                 evi_max_filename=None, evi_max_dir=None, evi_max_pattern=None,
                 evi_min_filename=None, evi_min_dir=None, evi_min_pattern=None,
                 dst_filename=None, dst_dir=None, dst_pattern=None):
        logger.info('entering calc_vci')
        if cur_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(cur_dir, cur_pattern)
            try:
                _cur_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching vegetation file in directory')
        else:
            _cur_filename = cur_filename

        _evi_max_filename = evi_max_filename
        if _evi_max_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(evi_max_dir, evi_max_pattern)
            try:
                _evi_max_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching EVI long-term maximum file in directory')

        _evi_min_filename = evi_min_filename
        if _evi_min_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(evi_min_dir, evi_min_pattern)
            try:
                _evi_min_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching EVI long-term minimum file in directory')

        if dst_filename is None:
            # get new filename from directory and pattern
            _dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(_cur_filename)[1], cur_pattern, dst_pattern))
        else:
            _dst_filename = dst_filename
        if not os.path.isdir(os.path.dirname(_dst_filename)):
            os.makedirs(os.path.dirname(_dst_filename))

        vegetation_analysis.calc_VCI(_cur_filename, _evi_max_filename, _evi_min_filename, _dst_filename)
        logger.info('leaving calc_vci')
        return None
