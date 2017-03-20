import vampire.VampireDefaults
import vampire.directory_utils
import vampire.filename_utils
import vampire.processing.raster_utils as raster_utils

import platform
platform = platform.system()
if platform == "Linux":
    import calculate_statistics_os as calculate_statistics
    import vegetation_analysis_os as vegetation_analysis
elif platform == "Windows":
    import calculate_statistics_arc as calculate_statistics
    import vegetation_analysis_arc as vegetation_analysis

class RasterProcessor:
    def __init__(self):
        # load default values from .ini file
        self.vampire = vampire.VampireDefaults.VampireDefaults()
        return

    def crop_files(self, input_dir, output_dir, boundary_file, file_pattern=None,
                   output_pattern=None, overwrite=False, nodata=True, logger=None):
        _patterns = (file_pattern, output_pattern)
        _gdal_path = self.vampire.get('directories', 'gdal_dir')
        raster_utils.crop_files(base_path=input_dir, output_path=output_dir, bounds=boundary_file,
                                tools_path=_gdal_path,
                                patterns=_patterns, overwrite=overwrite, nodata=nodata, logger=logger)
        return None
