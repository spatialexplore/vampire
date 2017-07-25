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

    def match_projection(self, master_file, master_dir, master_pattern,
                         slave_file, slave_dir, slave_pattern,
                         output_file, output_dir, output_pattern):
        if master_file is None:
            _file_list = vampire.directory_utils.get_matching_files(master_dir, master_pattern)
            if _file_list is not None:
                _master_file = _file_list[0]
            else:
                raise ValueError, "No matching master file found."
        else:
            _master_file = master_file

        if slave_file is None:
            _file_list = vampire.directory_utils.get_matching_files(slave_dir, slave_pattern)
            if _file_list is not None:
                _slave_file = _file_list[0]
            else:
                raise ValueError, "No matching slave file found."
        else:
            _slave_file = slave_file

        if output_file is not None:
            _output_file = output_file
            _output_dir = os.path.dirname(_output_file)
        else:
            if output_dir is None:
                raise ValueError, "No output directory provided."
            if output_pattern is None:
                raise ValueError, "No output pattern provided."
            _output_dir = output_dir
            _output_file = os.path.join(_output_dir, vampire.filename_utils.generate_output_filename(
                os.path.basename(_slave_file), slave_pattern, output_pattern, False))

        if not os.path.isdir(_output_dir):
            # need to create output dir
            os.makedirs(_output_dir)

        raster_utils.reproject_image_to_master(_master_file, _slave_file, _output_file)

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

    def calc_zonal_statistics(self, raster_file, raster_dir, raster_pattern,
                              polygon_file, polygon_dir, polygon_pattern,
                              zone_field, output_dir, output_file, output_pattern):

        if raster_file is None:
            _file_list = vampire.directory_utils.get_matching_files(raster_dir, raster_pattern)
            if _file_list is not None:
                _raster_file = _file_list[0]
            else:
                raise ValueError, "No matching raster file found."
        else:
            _raster_file = raster_file

        if polygon_file is None:
            _file_list = vampire.directory_utils.get_matching_files(polygon_dir, polygon_pattern)
            if _file_list is not None:
                _polygon_file = _file_list[0]
            else:
                raise ValueError, "No matching polygon file found."
        else:
            _polygon_file = polygon_file

        if output_file is None:
            if output_dir is None:
                raise ValueError, "No output directory provided."
            if output_pattern is None:
                raise ValueError, "No output pattern provided."
            _output_dir = output_dir
            _output_file = os.path.join(_output_dir, vampire.filename_utils.generate_output_filename(
                os.path.basename(_raster_file), raster_pattern, output_pattern, False))
        else:
            _output_file = output_file

        calculate_statistics.calc_zonal_statistics(raster_file=_raster_file, polygon_file=_polygon_file,
                                                   zone_field=zone_field, output_table=_output_file)

        return None

    def mask_by_shapefile(self, raster_file, raster_dir, raster_pattern,
                          polygon_file, polygon_dir, polygon_pattern,
                          output_file, output_dir, output_pattern, nodata=False, logger=None):
        if raster_file is None:
            _file_list = vampire.directory_utils.get_matching_files(raster_dir, raster_pattern)
            if _file_list is not None:
                _raster_file = _file_list[0]
            else:
                raise ValueError, "No matching raster file found."
        else:
            _raster_file = raster_file

        if polygon_file is None:
            _file_list = vampire.directory_utils.get_matching_files(polygon_dir, polygon_pattern)
            if _file_list is not None:
                _polygon_file = _file_list[0]
            else:
                raise ValueError, "No matching polygon file found."
        else:
            _polygon_file = polygon_file

        if output_file is None:
            if output_dir is None:
                raise ValueError, "No output directory provided."
            if output_pattern is None:
                raise ValueError, "No output pattern provided."
            _output_dir = output_dir
            _output_file = os.path.join(_output_dir, vampire.filename_utils.generate_output_filename(
                os.path.basename(_raster_file), raster_pattern, output_pattern, False))
        else:
            _output_file = output_file
        _gdal_path = self.vampire.get('directories', 'gdal_dir')

        raster_utils.mask_by_shapefile(raster_file=_raster_file, polygon_file=_polygon_file,
                                       output_file=_output_file, gdal_path=_gdal_path, nodata=nodata, logger=logger)

        return None