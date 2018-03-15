import logging
import os

import BaseTaskImpl
import directory_utils as directory_utils
import filename_utils as filename_utils

logger = logging.getLogger(__name__)
try:
    import temperature_analysis_arc as temperature_analysis
    import calculate_statistics_arc as calculate_statistics
except ImportError:
    import temperature_analysis_os as temperature_analysis
    import calculate_statistics_os as calculate_statistics

class TCITaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(TCITaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Rainfall Anomaly')
        return

    def process(self):
        logger.debug("Compute Temperature Condition Index")
        _cur_file = None
        _cur_dir = None
        _cur_pattern = None
        _lst_max_file = None
        _lst_min_file = None
        _lst_max_dir = None
        _lst_min_dir = None
        _lst_max_pattern = None
        _lst_min_pattern = None
        _output_file = None
        _output_dir = None
        _output_pattern = None
        _interval = None

        logger.debug("Compute Temperature Condition Index")
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
        if 'LST_max_file' in self.params:
            _lst_max_file = self.params['LST_max_file']
        else:
            if not 'LST_max_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No LST long-term maximum file 'LST_max_file' or pattern 'LST_max_pattern' specified.", None)
            else:
                if 'LST_max_dir' in self.params:
                    _lst_max_dir = self.params['LST_max_dir']
                else:
                    _lst_max_dir = None
                _lst_max_pattern = self.params['LST_max_pattern']

        if 'LST_min_file' in self.params:
            _lst_min_file = self.params['LST_min_file']
        else:
            if not 'LST_min_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No LST long-term minimum file 'LST_min_file' or pattern 'LST_min_pattern' specified.", None)
            else:
                if 'LST_min_dir' in self.params:
                    _lst_min_dir = self.params['LST_min_dir']
                else:
                    _lst_min_dir = None
                _lst_min_pattern = self.params['LST_min_pattern']
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
        if 'interval' in self.params:
            _interval = self.params['interval']

        self.calc_tci(cur_filename=_cur_file, cur_dir=_cur_dir, cur_pattern=_cur_pattern,
                    lst_max_filename=_lst_max_file, lst_max_dir=_lst_max_dir, lst_max_pattern=_lst_max_pattern,
                    lst_min_filename=_lst_min_file, lst_min_dir=_lst_min_dir, lst_min_pattern=_lst_min_pattern,
                    dst_filename=_output_file, dst_dir=_output_dir, dst_pattern=_output_pattern, interval=_interval
                    )

        return

    def calc_tci(self, cur_filename=None, cur_dir=None, cur_pattern=None,
                 lst_max_filename=None, lst_max_dir=None, lst_max_pattern=None,
                 lst_min_filename=None, lst_min_dir=None, lst_min_pattern=None,
                 dst_filename=None, dst_dir=None, dst_pattern=None, interval=None):
        logger.info('entering calc_tci')
        _temp_file = None
        if dst_dir is None:
            _dst_dir = self.vp.get('MODIS_VCI', 'vci_product_dir')
        else:
            _dst_dir = dst_dir
        if cur_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(cur_dir, cur_pattern)
            try:
                if files_list and len(files_list) > 1:
                    # more than one match - average files
                    print 'Found more than one matching temperature file in directory - averaging '
                    print files_list
                    _fn, _ext = os.path.splitext(os.path.basename(files_list[len(files_list)-1]))
                    _temp_file = os.path.join(_dst_dir, os.path.basename(files_list[len(files_list)-1]))
                    calculate_statistics.calc_average(files_list, _temp_file)
                    _cur_filename = _temp_file
                else:
                    _cur_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching temperature file in directory')
        else:
            if not isinstance(cur_filename, basestring) and isinstance(cur_filename, list):
                # cur_filename is a list - need to average
                print 'More than one current file provided - averaging '
                print cur_filename
                _temp_file = '{0}'.format(os.path.join(_dst_dir, os.path.basename(cur_filename[len(cur_filename)-1])))
                calculate_statistics.calc_average(cur_filename, _temp_file)
                _cur_filename = _temp_file
            else:
                _cur_filename = cur_filename

        _lst_max_filename = lst_max_filename
        if _lst_max_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(lst_max_dir, lst_max_pattern)
            try:
                _lst_max_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find LST long-term maximum file matching {0} in directory {1}'.format(lst_max_pattern, lst_max_dir))

        _lst_min_filename = lst_min_filename
        if _lst_min_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(lst_min_dir, lst_min_pattern)
            try:
                _lst_min_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching LST long-term minimum file in directory')

        if dst_filename is None:
            # get new filename from directory and pattern
            if cur_pattern is None:
                _cur_pattern = self.vp.get('MODIS_LST', 'lst_regional_pattern')
            else:
                _cur_pattern = cur_pattern
            _dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(_cur_filename)[1], _cur_pattern, dst_pattern))
        else:
            _dst_filename = dst_filename
        if not os.path.isdir(dst_dir):
            # make directory if not existing
            os.makedirs(dst_dir)

        temperature_analysis.calc_TCI(cur_filename=_cur_filename,
                                      lta_max_filename=_lst_max_filename,
                                      lta_min_filename=_lst_min_filename,
                                      dst_filename=_dst_filename
                                      )
        if _temp_file is not None:
            os.remove(os.path.join(_dst_dir, _temp_file))
        logger.info('leaving calc_tci')
        return None
