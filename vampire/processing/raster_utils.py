import os
import subprocess
import vampire.directory_utils as directory_utils
import vampire.filename_utils as filename_utils

def clip_raster_to_shp(shpfile, in_raster, out_raster, gdal_path, nodata=True, logger=None):
    # call gdalwarp to clip to shapefile
    try:
        if logger: logger.debug("%s",shpfile)
        if logger: logger.debug("%s",in_raster)
        if logger: logger.debug("%s",out_raster)
        gdal_exe = os.path.join(gdal_path, 'gdalwarp')
        if nodata:
            retcode = subprocess.call([gdal_exe, '-t_srs', 'EPSG:4326', '-dstnodata', '-9999', '-crop_to_cutline', '-cutline', shpfile, in_raster, out_raster])
        else:
            retcode = subprocess.call([gdal_exe, '-overwrite', '-t_srs', 'EPSG:4326', '-crop_to_cutline', '-cutline', shpfile, in_raster, out_raster])
#            print "gdalwarp -overwrite', '-t_srs', 'EPSG:4326', '-crop_to_cutline', '-cutline' {0}, {1}, {2}".format(shpfile, in_raster, out_raster)
        if logger: logger.debug("gdalwarp return code is %s", retcode)
    except subprocess.CalledProcessError as e:
        if logger: logger.error("Error in gdalwarp")
        if logger: logger.error("%s",e.output)
#        raise
    except Exception, e:
        if logger: logger.error("Warning in gdalwarp")
    return 0

def crop_files(base_path, output_path, bounds, tools_path, patterns = None, overwrite = False, nodata=True, logger = None):
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
            if logger: logger.debug("Cropping file: %s",ifl)
            if os.path.splitext(ifl)[1] == '.gz':
                # unzip first
                directory_utils.unzip_file_list([ifl])
                ifl = ifl[:-3] # remove .gz from filename
            clip_raster_to_shp(shpfile=bounds, in_raster=ifl, out_raster=_out_raster,
                               gdal_path=tools_path, nodata=nodata)
            _fileslist.append(_new_filename)
    return _fileslist
