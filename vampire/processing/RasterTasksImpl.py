import logging
import os

import processing.raster_utils as raster_utils

import BaseTaskImpl
import directory_utils
import filename_utils
import VampireDefaults as VampireDefaults

logger = logging.getLogger(__name__)
try:
    import calculate_statistics_arc as calculate_statistics
    import vegetation_analysis_arc as vegetation_analysis
except ImportError:
    import calculate_statistics_os as calculate_statistics
    import vegetation_analysis_os as vegetation_analysis

class RasterTasksImpl():
    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, process_type, params, vampire_defaults=None):
        if process_type not in cls.subclasses:
            raise ValueError('Bad process type {}'.format(process_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[process_type](params, vp)

@RasterTasksImpl.register_subclass('crop')
class RasterCropTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        super(RasterCropTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising MODIS download task')
        return

    def process(self):
        logger.debug("Crop raster data to boundary")

        if 'file_pattern' in self.params:
            _pattern = self.params['file_pattern']
        else:
            _pattern = None
        if 'output_pattern' in self.params:
            _out_pattern = self.params['output_pattern']
        else:
            _out_pattern = None
        if 'overwrite' in self.params:
            _overwrite = True
        else:
            _overwrite = False
        if 'no_data' in self.params:
            _no_data = True
        else:
            _no_data = False

        try:
            _input_dir = self.params['input_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No input directory 'input_dir' set.", e)
        try:
            _output_dir = self.params['output_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No output directory 'output_dir' set.", e)
        try:
            _boundary_file = self.params['boundary_file']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No boundary file specified.", e)
        self.crop_files(input_dir=_input_dir, output_dir=_output_dir, boundary_file=_boundary_file,
                      file_pattern=_pattern, output_pattern=_out_pattern, overwrite=_overwrite,
                      nodata=_no_data)
        return

    def crop_files(self, input_dir, output_dir, boundary_file, file_pattern=None,
                   output_pattern=None, overwrite=False, nodata=True):
        _patterns = (file_pattern, output_pattern)
        _gdal_path = self.vp.get('directories', 'gdal_dir')
        if not os.path.isdir(output_dir):
            # need to create output dir
            os.makedirs(output_dir)
        raster_utils.crop_files(base_path=input_dir, output_path=output_dir, bounds=boundary_file,
                                tools_path=_gdal_path,
                                patterns=_patterns, overwrite=overwrite, nodata=nodata)
        return None


@RasterTasksImpl.register_subclass('match_projection')
class RasterReprojectTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        super(RasterReprojectTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising MODIS download task')
        return

    def process(self):
        logger.debug("Reproject file to same extent and resolution as master")
        _master_filename = None
        _slave_filename = None
        _master_dir = None
        _master_pattern = None
        _slave_dir = None
        _slave_pattern = None
        _output_file = None
        _output_dir = None
        _output_pattern = None

        if 'master_file' in self.params:
            _master_filename = self.params['master_file']
        else:
            if not 'master_dir' in self.params:
                raise BaseTaskImpl.ConfigFileError("No master file 'master_file' or pattern 'master_pattern'/directory 'master_dir' specified.", None)
            else:
                _master_dir = self.params['master_dir']
                _master_pattern = self.params['master_pattern']
        if 'slave_file' in self.params:
            _slave_filename = self.params['slave_file']
        else:
            if not 'slave_dir' in self.params:
                raise BaseTaskImpl.ConfigFileError("No slave file 'slave_file' or pattern 'slave_pattern'/directory 'slave_dir' specified.", None)
            else:
                _slave_dir = self.params['slave_dir']
                _slave_pattern = self.params['slave_pattern']

        if 'output_file' in self.params:
            _output_file = self.params['output_file']
        else:
            if not 'output_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No output filename 'output_file' or output pattern 'output_pattern' specified.", None)
            else:
                _output_pattern = self.params['output_pattern']
                _output_dir = self.params['output_dir']

        self.match_projection(master_file=_master_filename, master_dir=_master_dir, master_pattern=_master_pattern,
                            slave_file=_slave_filename, slave_dir=_slave_dir, slave_pattern=_slave_pattern,
                            output_file=_output_file, output_dir=_output_dir, output_pattern=_output_pattern)

        return

    def match_projection(self, master_file, master_dir, master_pattern,
                         slave_file, slave_dir, slave_pattern,
                         output_file, output_dir, output_pattern):
        if master_file is None:
            _file_list = directory_utils.get_matching_files(master_dir, master_pattern)
            if _file_list is not None:
                _master_file = _file_list[0]
            else:
                raise ValueError, "No matching master file found."
        else:
            _master_file = master_file

        if slave_file is None:
            _file_list = directory_utils.get_matching_files(slave_dir, slave_pattern)
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
            _output_file = os.path.join(_output_dir, filename_utils.generate_output_filename(
                os.path.basename(_slave_file), slave_pattern, output_pattern, False))

        if not os.path.isdir(_output_dir):
            # need to create output dir
            os.makedirs(_output_dir)

        raster_utils.reproject_image_to_master(_master_file, _slave_file, _output_file)

        return None

@RasterTasksImpl.register_subclass('zonal_statistics')
class RasterZonalStatisticsTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        super(RasterZonalStatisticsTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising MODIS download task')
        return

    def process(self):
        logger.debug("Calculate zonal statistics as a table from raster and polygon")
        _raster_filename = None
        _polygon_filename = None
        _raster_dir = None
        _raster_pattern = None
        _polygon_dir = None
        _polygon_pattern = None
        _output_file = None
        _output_dir = None
        _output_pattern = None
        _zone_field = None

        if 'raster_file' in self.params:
            _raster_filename = self.params['raster_file']
        else:
            if not 'raster_dir' in self.params:
                raise BaseTaskImpl.ConfigFileError("No raster file 'raster_file' or pattern 'raster_pattern'/directory 'raster_dir' specified.", None)
            else:
                _raster_dir = self.params['raster_dir']
                _raster_pattern = self.params['raster_pattern']
        if 'polygon_file' in self.params:
            _polygon_filename = self.params['polygon_file']
        else:
            if not 'polygon_dir' in self.params:
                raise BaseTaskImpl.ConfigFileError("No polygon file 'polygon_file' or pattern 'polygon_pattern'/directory 'polygon_dir' specified.", None)
            else:
                _polygon_dir = self.params['polygon_dir']
                _polygon_pattern = self.params['polygon_pattern']

        if 'output_file' in self.params:
            _output_file = self.params['output_file']
        else:
            if not 'output_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No output filename 'output_file' or output pattern 'output_pattern' specified.", None)
            else:
                _output_pattern = self.params['output_pattern']
                _output_dir = self.params['output_dir']

        if 'zone_field' in self.params:
            _zone_field = self.params['zone_field']
        else:
            raise BaseTaskImpl.ConfigFileError("No zone field specified", None)

        self.calc_zonal_statistics(raster_file=_raster_filename, raster_dir=_raster_dir, raster_pattern=_raster_pattern,
                            polygon_file=_polygon_filename, polygon_dir=_polygon_dir, polygon_pattern=_polygon_pattern,
                            output_file=_output_file, output_dir=_output_dir, output_pattern=_output_pattern,
                            zone_field=_zone_field)

    def calc_zonal_statistics(self, raster_file, raster_dir, raster_pattern,
                              polygon_file, polygon_dir, polygon_pattern,
                              zone_field, output_dir, output_file, output_pattern):

        if raster_file is None:
            _file_list = directory_utils.get_matching_files(raster_dir, raster_pattern)
            if _file_list is not None:
                _raster_file = _file_list[0]
            else:
                raise ValueError, "No matching raster file found."
        else:
            _raster_file = raster_file

        if polygon_file is None:
            _file_list = directory_utils.get_matching_files(polygon_dir, polygon_pattern)
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
            _output_file = os.path.join(_output_dir, filename_utils.generate_output_filename(
                os.path.basename(_raster_file), raster_pattern, output_pattern, False))
        else:
            _output_file = output_file

        calculate_statistics.calc_zonal_statistics(raster_file=_raster_file, polygon_file=_polygon_file,
                                                   zone_field=zone_field, output_table=_output_file)

        return None


@RasterTasksImpl.register_subclass('apply_mask')
class RasterApplyMaskTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        super(RasterApplyMaskTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising MODIS download task')
        self.params = params
        self.vp = vampire_defaults
        return

    def process(self):
        logger.debug("Apply shapefile mask to raster")
        _raster_filename = None
        _polygon_filename = None
        _raster_dir = None
        _raster_pattern = None
        _polygon_dir = None
        _polygon_pattern = None
        _boundary_raster = None
        _boundary_raster_dir = None
        _boundary_raster_pattern = None
        _output_file = None
        _output_dir = None
        _output_pattern = None

        if 'raster_file' in self.params:
            _raster_filename = self.params['raster_file']
        else:
            if not 'raster_dir' in self.params:
                raise BaseTaskImpl.ConfigFileError("No raster file 'raster_file' or pattern 'raster_pattern'/directory 'raster_dir' specified.", None)
            else:
                _raster_dir = self.params['raster_dir']
                _raster_pattern = self.params['raster_pattern']
        if 'polygon_file' in self.params:
            _polygon_filename = self.params['polygon_file']
        else:
            if 'polygon_dir' in self.params:
                _polygon_dir = self.params['polygon_dir']
                _polygon_pattern = self.params['polygon_pattern']
            else:
                if 'boundary_raster' in self.params:
                    _boundary_raster = self.params['boundary_raster']
                else:
                    if 'boundary_dir' in self.params:
                        _boundary_raster_dir = self.params['boundary_raster_dir']
                        _boundary_raster_pattern = self.params['boundary_raster_pattern']
                    else:
                        raise BaseTaskImpl.ConfigFileError("No polygon file or raster boundary specified")

        if 'output_file' in self.params:
            _output_file = self.params['output_file']
        else:
            if not 'output_pattern' in self.params:
                raise BaseTaskImpl.ConfigFileError("No output filename 'output_file' or output pattern 'output_pattern' specified.", None)
            else:
                _output_pattern = self.params['output_pattern']
                _output_dir = self.params['output_dir']
        if 'no_data' in self.params:
            _no_data = True
        else:
            _no_data = False

        if _boundary_raster is not None:
            self.mask_by_raster(raster_file=_raster_filename, raster_dir=_raster_dir, raster_pattern=_raster_pattern,
                                boundary_raster=_boundary_raster, boundary_raster_dir=_boundary_raster_dir,
                                boundary_raster_pattern=_boundary_raster_pattern,
                                output_file=_output_file, output_dir=_output_dir, output_pattern=_output_pattern,
                                nodata=_no_data)
        else:
            self.mask_by_shapefile(raster_file=_raster_filename, raster_dir=_raster_dir, raster_pattern=_raster_pattern,
                                 polygon_file=_polygon_filename, polygon_dir=_polygon_dir, polygon_pattern=_polygon_pattern,
                                 output_file=_output_file, output_dir=_output_dir, output_pattern=_output_pattern,
                                 nodata=_no_data)

    def mask_by_shapefile(self, raster_file, raster_dir, raster_pattern,
                          polygon_file, polygon_dir, polygon_pattern,
                          output_file, output_dir, output_pattern, nodata=False):
        if raster_file is None:
            _file_list = directory_utils.get_matching_files(raster_dir, raster_pattern)
            if _file_list:
                _raster_file = _file_list[0]
            else:
                raise ValueError, "No matching raster file found."
        else:
            _raster_file = raster_file

        if polygon_file is None:
            _file_list = directory_utils.get_matching_files(polygon_dir, polygon_pattern)
            if _file_list is not None:
                _polygon_file = _file_list[0]
            else:
                raise ValueError, "No matching polygon file or polygon dir/pattern found."
        else:
            _polygon_file = polygon_file

        if output_file is None:
            if output_dir is None:
                raise ValueError, "No output directory provided."
            if output_pattern is None:
                raise ValueError, "No output pattern provided."
            _output_dir = output_dir
            _output_file = os.path.join(_output_dir, filename_utils.generate_output_filename(
                os.path.basename(_raster_file), raster_pattern, output_pattern, False))
        else:
            _output_file = output_file
        _gdal_path = self.vp.get('directories', 'gdal_dir')


        raster_utils.mask_by_shapefile(raster_file=_raster_file, polygon_file=_polygon_file,
                                       output_file=_output_file, gdal_path=_gdal_path, nodata=nodata)

        return None

    def mask_by_raster(self, raster_file, raster_dir, raster_pattern, boundary_raster, boundary_raster_dir,
                       boundary_raster_pattern, output_file, output_dir, output_pattern, nodata=False):
        if raster_file is None:
            _file_list = directory_utils.get_matching_files(raster_dir, raster_pattern)
            if _file_list:
                _raster_file = _file_list[0]
            else:
                raise ValueError, "No matching raster file found."
        else:
            _raster_file = raster_file

        if boundary_raster is None:
            _file_list = directory_utils.get_matching_files(boundary_raster_dir, boundary_raster_pattern)
            if _file_list is not None:
                _boundary_raster = _file_list[0]
            else:
                raise ValueError, "No matching raster boundary file or boundary dir/pattern found."
        else:
            _boundary_raster = boundary_raster

        if output_file is None:
            if output_dir is None:
                raise ValueError, "No output directory provided."
            if output_pattern is None:
                raise ValueError, "No output pattern provided."
            _output_dir = output_dir
            _output_file = os.path.join(_output_dir, filename_utils.generate_output_filename(
                os.path.basename(_raster_file), raster_pattern, output_pattern, False))
        else:
            _output_file = output_file

        raster_utils.mask_by_raster(raster_file=_raster_file, mask_file=_boundary_raster, output_file=_output_file)
        return None


@RasterTasksImpl.register_subclass('mosaic')
class RasterMosaicTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RasterMosaicTask object.

    Implementation class for generating a mosaic from a list of rasters.

    """
    def __init__(self, params, vampire_defaults):
        super(RasterMosaicTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising raster mosaic task')
        self.params = params
        self.vp = vampire_defaults
        return

    def process(self):
        logger.debug("Mosaic list of rasters")
        _input_dir = None
        _file_pattern = None
        _output_dir = None
        _output_pattern = None
        _mosaic_method = None

        if 'input_dir' in self.params:
            _input_dir = self.params['input_dir']
        else:
            raise BaseTaskImpl.ConfigFileError("No input directory 'input_dir' specified.", None)
        if 'file_pattern' in self.params:
            _file_pattern = self.params['file_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError("No file pattern 'file_pattern' specified.", None)
        if 'output_dir' in self.params:
            _output_dir = self.params['output_dir']
        else:
            raise BaseTaskImpl.ConfigFileError("No output directory 'output_dir' specified.", None)
        if 'output_pattern' in self.params:
            _output_pattern = self.params['output_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError("No output pattern 'output_pattern' specified.", None)
        if 'mosaic_method' in self.params:
            _mosaic_method = self.params['mosaic_method']
        else:
            _mosaic_method = 'MAXIMUM'

        _file_list = directory_utils.get_matching_files(_input_dir, _file_pattern)
        if not _file_list:
           raise ValueError, "No matching raster file found."

        _base_name = os.path.basename(_file_list[0])
        _output_file = filename_utils.generate_output_filename(_base_name, _file_pattern,
                                                                       _output_pattern, False)

        _file_str = ','.join(map(str, _file_list))
        calculate_statistics.mosaic_rasters(_file_list, _output_dir, _output_file, _mosaic_method)

        return None

