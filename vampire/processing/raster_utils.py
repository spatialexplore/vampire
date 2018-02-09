import logging
import os
import subprocess

import gdal
import numpy as np

import directory_utils as directory_utils
import filename_utils as filename_utils

logger = logging.getLogger(__name__)

def clip_raster_to_shp(shpfile, in_raster, out_raster, gdal_path, nodata=True):
    # call gdalwarp to clip to shapefile
    try:
        logger.debug("%s",shpfile)
        logger.debug("%s",in_raster)
        logger.debug("%s",out_raster)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        if nodata:
            retcode = subprocess.call([gdal_exe, '-t_srs', 'EPSG:4326', '-dstnodata', '-9999', '--config', 'GDALWARP_IGNORE_BAD_CUTLINE', 'YES', '-crop_to_cutline', '-cutline', shpfile, in_raster, out_raster])
        else:
            retcode = subprocess.call([gdal_exe, '-overwrite', '-t_srs', 'EPSG:4326', '--config', 'GDALWARP_IGNORE_BAD_CUTLINE', 'YES', '-crop_to_cutline', '-cutline', shpfile, in_raster, out_raster])
#            print "gdalwarp -overwrite', '-t_srs', 'EPSG:4326', '-crop_to_cutline', '-cutline' {0}, {1}, {2}".format(shpfile, in_raster, out_raster)
        logger.debug("gdalwarp return code is %s", retcode)
    except subprocess.CalledProcessError as e:
        logger.error("Error in gdalwarp")
        logger.error("%s",e.output)
#        raise
    except Exception, e:
        logger.error("Warning in gdalwarp")
    return 0

def crop_files(base_path, output_path, bounds, tools_path, patterns = None, overwrite = False, nodata=True):
#    import re
    _fileslist = []
    if not patterns[0]:
        # if no pattern, try all files
        _p = '*'
    else:
        _p = patterns[0]

    _all_files = directory_utils.get_matching_files(base_path, _p)

    for ifl in _all_files:
        _f= os.path.basename(os.path.basename(ifl))
#        m = re.match(_p, _f)
        _new_filename = filename_utils.generate_output_filename(input_filename=_f, in_pattern=_p,
                                                                out_pattern=patterns[1], ignore_leap_year=False)
        _out_raster = os.path.join(output_path, _new_filename)

        if not os.path.exists(_out_raster) or overwrite == True:
            # crop file here
            logger.debug("Cropping file: %s",ifl)
            if os.path.splitext(ifl)[1] == '.gz':
                # unzip first
                directory_utils.unzip_file_list([ifl])
                ifl = ifl[:-3] # remove .gz from filename
            clip_raster_to_shp(shpfile=bounds, in_raster=ifl, out_raster=_out_raster,
                               gdal_path=tools_path, nodata=nodata)
            _fileslist.append(_new_filename)
    return _fileslist

def reproject_image_to_master ( master, slave, output, res=None, nodata=0.0 ):
    """This function reprojects an image (``slave``) to
    match the extent, resolution and projection of another
    (``master``) using GDAL. The newly reprojected image
    is a GDAL VRT file for efficiency. A different spatial
    resolution can be chosen by specifyign the optional
    ``res`` parameter. The function returns the new file's
    name.
    Parameters
    -------------
    master: str 
        A filename (with full path if required) with the 
        master image (that that will be taken as a reference)
    slave: str 
        A filename (with path if needed) with the image
        that will be reprojected
    res: float, optional
        The desired output spatial resolution, if different 
        to the one in ``master``.
    Returns
    ----------
    The reprojected filename
    TODO Have a way of controlling output filename
    """
    slave_ds = gdal.Open( slave )
    if slave_ds is None:
        raise IOError, "GDAL could not open slave file %s " \
            % slave
    slave_proj = slave_ds.GetProjection()
    slave_geotrans = slave_ds.GetGeoTransform()
    data_type = slave_ds.GetRasterBand(1).DataType
    n_bands = slave_ds.RasterCount

    master_ds = gdal.Open( master )
    if master_ds is None:
        raise IOError, "GDAL could not open master file %s " \
            % master
    master_proj = master_ds.GetProjection()
    master_geotrans = master_ds.GetGeoTransform()
    w = master_ds.RasterXSize
    h = master_ds.RasterYSize
    if res is not None:
        master_geotrans[1] = float( res )
        master_geotrans[-1] = - float ( res )

    if output is None:
        dst_filename = slave.replace( ".tif", "_crop.tif" )
    else:
        dst_filename = output
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst_filename,
                                                w, h, n_bands, data_type)
    dst_ds.SetGeoTransform( master_geotrans )
    dst_ds.SetProjection( master_proj)

    gdal.ReprojectImage( slave_ds, dst_ds, slave_proj,
                         master_proj, gdal.GRA_NearestNeighbour)

    if nodata is None:
        nodata = 0.0
    dst_ds.GetRasterBand(1).SetNoDataValue(nodata) #slave_ds.GetRasterBand(1).GetNoDataValue())
    dst_ds = None  # Flush to disk
    # with rasterio.open(dst_filename) as dst_r:
    #     profile = dst_r.profile.copy()
    #     _dst_a = dst_r.read(1, masked=True)
    #     _dst_a.filled(fill_value=-9999)
    #     profile.update(nodata=-9999)
    #     with rasterio.open(dst_filename, 'w', **profile) as dst:
    #         dst.write(_dst_a.astype(rasterio.float32), 1)

    return dst_filename


def reproject_cut ( slave, box=None, t_srs=None, s_srs=None, res=None ):
    """This function reprojects an image (``slave``) to
    match the extent, resolution and projection of another
    (``master``) using GDAL. The newly reprojected image
    is a GDAL VRT file for efficiency. A different spatial
    resolution can be chosen by specifyign the optional
    ``res`` parameter. The function returns the new file's
    name.
    Parameters
    -------------
    master: str 
        A filename (with full path if required) with the 
        master image (that that will be taken as a reference)
    slave: str 
        A filename (with path if needed) with the image
        that will be reprojected
    res: float, optional
        The desired output spatial resolution, if different 
        to the one in ``master``.
    Returns
    ----------
    The reprojected filename
    TODO Have a way of controlling output filename
    """

    slave_ds = gdal.Open( slave )
    if slave_ds is None:
        raise IOError, "GDAL could not open slave file %s " \
            % slave
    if s_srs is None:
        proj = slave_ds.GetProjection()
    else:
        proj = s_srs

    slave_geotrans = slave_ds.GetGeoTransform()
    if box is None:
        ulx = slave_geotrans[0]
        uly = slave_geotrans[3]
        lrx = slave_geotrans[0] + slave_ds.RasterXSize * slave_geotrans[1]
        lry = slave_geotrans[3] + slave_ds.RasterySize * slave_geotrans[-1]
    else:
        ulx, uly, lrx, lry = box
    if res is None:
        res = slave_geotrans[1]

    data_type = slave_ds.GetRasterBand(1).DataType
    n_bands = slave_ds.RasterCount

    if t_srs is None:
        master_proj = proj
    else:
        master_proj = t_srs

    master_geotrans = [ ulx, res, slave_geotrans[2],
                        uly, slave_geotrans[4], -res ]

    w = int(np.round((lrx - ulx) / res))
    h = int(np.round((uly - lry) / res))

    dst_filename = slave.replace( ".TIF", "_crop.tif" )
    if dst_filename == slave:
        dst_filename = slave.replace( ".tif", "_crop.tif" )
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst_filename,
                                                  w, h, n_bands, data_type)
    dst_ds.SetGeoTransform( master_geotrans )
    dst_ds.SetProjection( proj )

    gdal.ReprojectImage( slave_ds, dst_ds, proj,
                         master_proj, gdal.GRA_NearestNeighbour)
    dst_ds = None  # Flush to disk
    return dst_filename

def mask_by_raster(raster_file, mask_file, output_file, nodata=None):
    try:
        import arcpy
        _cellsize = arcpy.env.cellSize
        arcpy.env.cellSize = "MINOF"
        _raster = arcpy.sa.Raster(raster_file)
        _mask_file = arcpy.sa.Raster(mask_file)
        _output = arcpy.sa.Times(_raster, _mask_file)
        _output.save(output_file)
        arcpy.env.cellSize = _cellsize
    except ImportError:
        raise ValueError("Error, mask by raster not implemented yet" )


def mask_by_shapefile(raster_file, polygon_file, output_file, gdal_path, nodata=None):
    try:
        logger.debug("%s", polygon_file)
        logger.debug("%s", raster_file)
        logger.debug("%s", output_file)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        if nodata:
            retcode = subprocess.call(
                [gdal_exe, '-overwrite', '-dstnodata', '-9999', '--config', 'GDALWARP_IGNORE_BAD_CUTLINE', 'YES',
                 '-cutline', polygon_file, raster_file, output_file])
        else:
            retcode = subprocess.call(
                [gdal_exe, '-overwrite', '--config', 'GDALWARP_IGNORE_BAD_CUTLINE', 'YES',
                 '-crop_to_cutline', '-cutline', polygon_file, raster_file, output_file])
        logger.debug("gdalwarp return code is %s", retcode)
    except subprocess.CalledProcessError as e:
        logger.error("Error in gdalwarp")
        logger.error("%s", e.output)
        #        raise
    except Exception, e:
        logger.error("Warning in gdalwarp")

    return None

try:
    import arcpy
    def mask_by_shapefile_arc(raster_file, polygon_file, output_file, gdal_path, nodata=None):

        return
except ImportError:
    def mask_by_shapefile_os(raster_file, polygon_file, output_file, gdal_path, nodata=None):
        try:
            logger.debug("%s", polygon_file)
            logger.debug("%s", raster_file)
            logger.debug("%s", output_file)
            gdal_exe = os.path.join(gdal_path, 'gdalwarp')
            if nodata:
                retcode = subprocess.call(
                    [gdal_exe, '-overwrite', '-dstnodata', '-9999', '--config', 'GDALWARP_IGNORE_BAD_CUTLINE', 'YES',
                     '-cutline', polygon_file, raster_file, output_file])
            else:
                retcode = subprocess.call(
                    [gdal_exe, '-overwrite', '--config', 'GDALWARP_IGNORE_BAD_CUTLINE', 'YES',
                     '-crop_to_cutline', '-cutline', polygon_file, raster_file, output_file])
            logger.debug("gdalwarp return code is %s", retcode)
        except subprocess.CalledProcessError as e:
            logger.error("Error in gdalwarp")
            logger.error("%s", e.output)
            #        raise
        except Exception, e:
            logger.error("Warning in gdalwarp")

        return None
