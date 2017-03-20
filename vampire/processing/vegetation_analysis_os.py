import gdal, osr
import numpy as np
import rasterio
#from rasterio.warp import reproject, RESAMPLING
import urllib2
import raster_utils


def calc_TCI(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    # calculate Temperature Condition Index
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)

    with rasterio.open(cur_filename) as cur_r:
        _cur_band = cur_r.read(1, masked=True)
        _profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_max_filename) as _lta_max_r:
            _lta_max_a = _lta_max_r.read(1, masked=True)
            with rasterio.open(lta_min_filename) as _lta_min_r:
                _lta_min_a = _lta_min_r.read(1, masked=True)
                _dst_f = np.zeros(_cur_band.shape)
                _newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_cur_band), np.ma.getmask(_lta_max_a)),
                                            _dst_f)
                _numerator=(_lta_max_a - _cur_band)
                _denominator = (_lta_max_a - _lta_min_a)
                _newd_f += (np.divide(_numerator, _denominator) * 100.0)

                _res = _newd_f.filled(fill_value=cur_r.nodata)
                _res2 = np.ma.masked_where(_res == cur_r.nodata, _res)

                _profile.update(dtype=rasterio.float64)
                with rasterio.open(dst_filename, 'w', **_profile) as _dst:
                    _dst.write(_res2.astype(rasterio.float64), 1)
    return None

def calc_VCI(cur_filename, evi_max_filename, evi_min_filename, dst_filename):
    # calculate Vegetation Condition Index
    # VCI = 100 x (EVI - EVI_min)/(EVI_max - EVI_min)
    with rasterio.open(cur_filename) as _cur_r:
        _cur_band = _cur_r.read(1, masked=True)
        _profile = _cur_r.profile.copy()
        print _cur_r.nodatavals
        with rasterio.open(evi_max_filename) as _evi_max_r:
#            evi_max_a = evi_max_r.read(1, masked=True)
            _evi_max_w = _evi_max_r.read(1, window=((0, _cur_band.shape[0]), (0, _cur_band.shape[1])), masked=True)
            with rasterio.open(evi_min_filename) as _evi_min_r:
#                evi_min_a = evi_min_r.read(1, masked=True)
                _evi_min_w = _evi_min_r.read(1, window=((0, _cur_band.shape[0]), (0, _cur_band.shape[1])), masked=True)
                _dst_f = np.zeros(_cur_band.shape)
                _newd_f = np.ma.masked_where(np.ma.getmask(_cur_band),
                                            _dst_f)
#                evi_min_ma = np.ma.masked_where(np.ma.getmask(cur_band), evi_min_w)
                # newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(cur_band), np.ma.getmask(evi_max_a)),
                #                             dst_f)
                _numerator = (_cur_band - _evi_min_w)
                _denominator = (_evi_max_w - _evi_min_w)
                with np.errstate(divide='ignore'):
                    _newd_f += (np.divide(_numerator, _denominator) * 100.0)
                _res = _newd_f.filled(fill_value=_cur_r.nodata)
                _res2 = np.ma.masked_where(_res == _cur_r.nodata, _res)

                _profile.update(dtype=rasterio.float64)
                with rasterio.open(dst_filename, 'w', **_profile) as _dst:
                    _dst.write(_res2.astype(rasterio.float64), 1)
    return None

def calc_VHI(vci_filename, tci_filename, dst_filename):
    # arcpy-free version
    # calculate Vegetation Health Index
    # VHI = 0.5 x (VCI + TCI)
    with rasterio.open(vci_filename) as _vci_r:
        _vci_a = _vci_r.read(1, masked=True)
        print _vci_r.nodatavals
        with rasterio.open(tci_filename) as _tci_r:
            _tci_a = _tci_r.read(1, masked=True)
            _profile = _tci_r.profile.copy()
            # check that resolution of vci matches resolution of tci
            print _vci_a.shape
            print _tci_a.shape
            if _vci_a.shape[0] > _tci_a.shape[0] or _vci_a.shape[1] > _tci_a.shape[1]:
                # resample vci
                _newarr = np.empty(shape=(_tci_a.shape[0], _tci_a.shape[1]))
                # adjust the new affine transform to the smaller cell size
                _aff = _vci_r.transform
                _newaff = rasterio.Affine(_aff[0] / (float(_tci_a.shape[0]) / float(_vci_a.shape[0])), _aff[1], _aff[2],
                                _aff[3], _aff[4] / (float(_tci_a.shape[1]) / float(_vci_a.shape[1])), _aff[5])

                try:
                    rasterio.warp.reproject(
                        _vci_a, _newarr,
                        src_transform=_aff,
                        dst_transform=_newaff,
                        src_crs=_vci_r.crs,
                        dst_crs=_vci_r.crs,
                        resampling=rasterio.warp.RESAMPLING.bilinear)
                except Exception, e:
                    print "Error in reproject "
                vci_a = np.ma.masked_where(np.ma.getmask(_tci_a), _newarr)
#                rasterUtils.resampleRaster(vci_filename, tmp_filename, gdal_path, tci_a.shape[0], tci_a.shape[1])
            elif _tci_a.shape[0] > _vci_a.shape[0] or _tci_a.shape[1] > _tci_a.shape[1]:
                # resample tci
                _newarr = np.empty(shape=(_vci_a.shape[0], _vci_a.shape[1]))
                # adjust the new affine transform to the smaller cell size
                _aff = _tci_a.transform
                _newaff = rasterio.Affine(_aff.a / (_vci_a.shape[0] / _tci_a.shape[0]), _aff.b, _aff.c,
                                         _aff.d, _aff.e / (_vci_a.shape[1] / _tci_a.shape[1]), _aff.f)
                try:
                    rasterio.warp.reproject(
                        _tci_a, _newarr,
                        src_transform=_aff,
                        dst_transform=_newaff,
                        src_crs=_tci_a.crs,
                        dst_crs=_tci_a.crs,
                        resample=rasterio.warp.RESAMPLING.bilinear)
                except Exception, e:
                    print "Error in reproject "
                _tci_a = np.ma.masked_where(np.ma.getmask(_vci_a), _newarr)

            _dst_f = np.zeros(_vci_a.shape)
            _newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_vci_a), np.ma.getmask(_tci_a)),
                                        _dst_f)
            _newd_f += ((_vci_a + _tci_a) * 0.5)
            _res = _newd_f.filled(fill_value=_vci_r.nodata)
            _res2 = np.ma.masked_where(_res == _vci_r.nodata, _res)
            _profile.update(dtype=rasterio.float64, nodata=-9999)
            with rasterio.open(dst_filename, 'w', **_profile) as _dst:
                _dst.write(_res2.astype(rasterio.float64), 1)
    return None