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

class VHITaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(VHITaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Vegetation Health Index task')
        return

    def process(self):
        logger.debug("Compute Vegetation Health Index")
        _vci_file = None
        _vci_dir = None
        _vci_pattern = None
        _tci_file = None
        _tci_dir = None
        _tci_pattern = None
        _out_file = None
        _output_dir = None
        _output_pattern = None

        if 'VCI_file' in self.params:
            _vci_file = self.params['VCI_file']
        else:
            if not 'VCI_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No VCI file 'VCI_file' or pattern 'VCI_pattern' specified.", None)
            else:
                if 'VCI_dir' in self.params:
                    _vci_dir = self.params['VCI_dir']
                else:
                    _vci_dir = None
                _vci_pattern = self.params['VCI_pattern']
        if 'TCI_file' in self.params:
            _tci_file = self.params['TCI_file']
        else:
            if not 'TCI_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No TCI file 'TCI_file' or pattern 'TCI_pattern' specified.", None)
            else:
                if 'TCI_dir' in self.params:
                    _tci_dir = self.params['TCI_dir']
                else:
                    _tci_dir = None
                _tci_pattern = self.params['TCI_pattern']
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

        self.calc_vhi(vci_filename=_vci_file, vci_dir=_vci_dir, vci_pattern=_vci_pattern,
                    tci_filename=_tci_file, tci_dir=_tci_dir, tci_pattern=_tci_pattern,
                    dst_filename=_out_file, dst_dir=_output_dir, dst_pattern=_output_pattern)

    def calc_vhi(self, vci_filename=None, vci_dir=None, vci_pattern=None,
                 tci_filename=None, tci_dir=None, tci_pattern=None,
                 dst_filename=None, dst_dir=None, dst_pattern=None):
        logger.info('entering calc_vhi')
        if vci_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(vci_dir, vci_pattern)
            try:
                _vci_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching Vegetation Condition Index file in directory')
        else:
            _vci_filename = vci_filename
        if tci_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(tci_dir, tci_pattern)
            try:
                _tci_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching Temperature Condition Index file in directory')
        else:
            _tci_filename = tci_filename
        if dst_filename is None:
            # get new filename from directory and pattern
            _dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(_vci_filename)[1], vci_pattern, dst_pattern))
        else:
            _dst_filename = dst_filename
        if dst_dir is not None and not os.path.isdir(dst_dir):
            # destination directory does not exist, create it first
            os.makedirs(dst_dir)
        vegetation_analysis.calc_VHI(vci_filename=_vci_filename,
                                     tci_filename=_tci_filename,
                                     dst_filename=_dst_filename
                                     )
        logger.info('leaving calc_vhi')
        return None
