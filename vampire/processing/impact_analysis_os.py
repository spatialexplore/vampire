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

def calc_field(table_name, new_field, cal_field, multiplier=1.0, type='DOUBLE'):
    base,ext = os.path.splitext(table_name)
    if ext == '.csv':
        _new_csv = []
        with open(table_name, 'rb') as cf:
            _reader = csv.reader(cf)
            _header_row = next(_reader)
            _header_row.append(new_field)
            _calc_index = 0
            try:
                _calc_index = _header_row.index(cal_field.lower())
            except ValueError, e:
                print '{0} not found in file header row.'.format(cal_field)
                return None
            for row in _reader:
                _new_row = row
                _val = float(row[_calc_index])
                _new_row.append(int(_val*multiplier))
#                print _new_row
                _new_csv.append(_new_row)
        with open(table_name, 'wb') as wf:
            wr = csv.writer(wf)
            wr.writerow(_header_row)
            wr.writerows(_new_csv)
    return None



    #     print db
    # if type == 'DOUBLE':
    #     db.addField(new_field, 'F')
    # elif type == 'LONG':
    #     db.addField(new_field, 'N')
    # for rec in db:
    #     rec[new_field] = rec[calc_field]*multiplier
    #     rec.store()
    # db.close()
#    return None