import rasterio
import rasterstats
import gdal
import numpy as np
import dbfpy.dbf
import raster_utils
import os
import csv

def reclassify_raster(raster, threshold, output_raster):
    _threshold = int(threshold)
    with rasterio.open(raster) as ras_r:
        _profile = ras_r.profile.copy()
        _ras_a = ras_r.read(1, masked=True)
        _dst_r = np.ma.masked_where(_ras_a > _threshold, _ras_a)
        _dst_r.data[_ras_a <= _threshold] = 1
        _dst_r = _dst_r.filled(-9999)
        _profile.update(dtype=rasterio.float32, nodata=-9999)
        with rasterio.open(output_raster, 'w', **_profile) as dst:
            dst.write(_dst_r.astype(rasterio.float32), 1)

    # _driver = gdal.GetDriverByName('GTiff')
    # _file = gdal.Open(raster)
    # _band = _file.GetRasterBand(1)
    # _ras_a = _band.ReadAsArray()
    #
    # _ras_a[np.where(_ras_a <= int(threshold))] = 1
    # _ras_a[np.where(_ras_a > int(threshold))] = -3000
    #
    # _out = _driver.Create(output_raster, _file.RasterXSize, _file.RasterYSize, 1)
    # _out.GetRasterBand(1).WriteArray(_ras_a)
    # _proj = _file.GetProjection()
    # _georef = _file.GetGeoTransform()
    # _out.SetProjection(_proj)
    # _out.SetGeoTransform(_georef)
    # _out.FlushCache()

    return None

def multiply_by_mask(raster, mask, output_raster):
    _tmp_ras = os.path.join(os.path.dirname(raster), 'tmp_{0}'.format(os.path.basename(raster)))
    raster_utils.reproject_image_to_master(master=mask, slave=raster, output=_tmp_ras)

    with rasterio.open(_tmp_ras) as ras:
        _ras_a = ras.read(1, masked=True)
        _profile = ras.profile.copy()
        with rasterio.open(mask) as _mask_r:
            # TODO check if same size/projection
            _mask_a = _mask_r.read(1, masked=True)
            _dst_r = np.multiply(_ras_a,_mask_a)
            _dst_r = _dst_r.filled(-9999)
            _profile.update(dtype=rasterio.float32, nodata=-9999)
            with rasterio.open(output_raster, 'w', **_profile) as dst:
                dst.write(_dst_r.astype(rasterio.float32), 1)
                print "saved multiply result in: ", output_raster
    return None

