import rasterio
import rasterstats
import gdal
import numpy as np
import dbfpy.dbf

def reclassify_raster(raster, threshold, output_raster):
    _driver = gdal.GetDriverByName('GTiff')
    _file = gdal.Open(raster)
    _band = _file.GetRasterBand(1)
    _ras_a = _band.ReadAsArray()

    _ras_a[np.where(_ras_a <= threshold)] = 1
    _ras_a[np.where(_ras_a > threshold)] = 0

    _out = _driver.Create(output_raster, _file.RasterXSize, _file.RasterYSize, 1)
    _out.GetRasterBand(1).WriteArray(_ras_a)
    _proj = _file.GetProjection()
    _georef = _file.GetGeoTransform()
    _out.SetProjection(_proj)
    _out.SetGeoTransform(_georef)
    _out.FlushCache()

    return None

def multiply_by_mask(raster, mask, output_raster):
    with rasterio.open(raster) as ras:
        _ras_a = ras.read(1, masked=True)
        profile = ras.profile.copy()
        with rasterio.open(mask) as mask:
            # TODO check if same size/projection
            _mask_a = mask.read(1, masked=True)
            _dst_r = _ras_a * _mask_a
            with rasterio.open(output_raster, 'w', **profile) as dst:
                dst.write(_dst_r.astype(profile.dtype), 1)
                print "saved multiply result in: ", output_raster
    return None

def calc_field(table_name, new_field, calc_field, multiplier=1.0, type='DOUBLE'):
    db = dbfpy.dbf.Dbf(table_name)
    print db
    if type == 'DOUBLE':
        db.addField(new_field, 'F')
    elif type == 'LONG':
        db.addField(new_field, 'N')
    for rec in db:
        rec[new_field] = rec[calc_field]*multiplier
        rec.store()
    db.close()
    return None