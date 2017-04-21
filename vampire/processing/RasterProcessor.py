import vampire.VampireDefaults
import vampire.directory_utils
import vampire.filename_utils
import vampire.processing.raster_utils as raster_utils

import os
# import platform
# platform = platform.system()
# if platform == "Linux":
#     import calculate_statistics_os as calculate_statistics
#     import vegetation_analysis_os as vegetation_analysis
# elif platform == "Windows":
#     import calculate_statistics_arc as calculate_statistics
#     import vegetation_analysis_arc as vegetation_analysis

try:
    import calculate_statistics_arc as calculate_statistics
    import vegetation_analysis_arc as vegetation_analysis
except ImportError:
    import calculate_statistics_os as calculate_statistics
    import vegetation_analysis_os as vegetation_analysis


class RasterProcessor:
    def __init__(self):
        # load default values from .ini file
        self.vampire = vampire.VampireDefaults.VampireDefaults()
        return

    def crop_files(self, input_dir, output_dir, boundary_file, file_pattern=None,
                   output_pattern=None, overwrite=False, nodata=True, logger=None):
        _patterns = (file_pattern, output_pattern)
        _gdal_path = self.vampire.get('directories', 'gdal_dir')
        if not os.path.isdir(output_dir):
            # need to create output dir
            os.makedirs(output_dir)
        raster_utils.crop_files(base_path=input_dir, output_path=output_dir, bounds=boundary_file,
                                tools_path=_gdal_path,
                                patterns=_patterns, overwrite=overwrite, nodata=nodata, logger=logger)
        return None

    # def average_files(self, input_dir, input_pattern, output_dir, output_pattern):
    #     if not os.path.isdir(output_dir):
    #         # need to create output dir
    #         os.makedirs(output_dir)
    #     _file_list = vampire.directory_utils.get_matching_files(input_dir, input_pattern)
    #     if _file_list is None:
    #         # no files found
    #         raise
    #     _output_file = vampire.filename_utils.generate_output_filename(input_filename=_file_list[0],
    #                                                                    in_pattern=input_pattern,
    #                                                                    out_pattern=output_pattern)
    #     calculate_statistics.calc_average(file_list=_file_list, avg_file=_output_file)
    #
    #     return None