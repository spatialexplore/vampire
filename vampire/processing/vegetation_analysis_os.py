import gdal, osr
import numpy as np
import rasterio
import rasterio.warp
#from rasterio.warp import reproject, RESAMPLING
import urllib2
import raster_utils
import logging
logger = logging.getLogger(__name__)


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
        _profile = _cur_r.profile.copy()
        print _cur_r.nodatavals
        _min_width = _cur_r.width
        _min_height = _cur_r.height
        with rasterio.open(evi_max_filename) as _evi_max_r:
#            evi_max_a = evi_max_r.read(1, masked=True)
            if _evi_max_r.width < _min_width:
                _min_width = _evi_max_r.width
            if _evi_max_r.height < _min_height:
                _min_height = _evi_max_r.height
            _evi_max_w = _evi_max_r.read(1, window=((0, _min_height), (0, _min_width)), masked=True)
            with rasterio.open(evi_min_filename) as _evi_min_r:
#                evi_min_a = evi_min_r.read(1, masked=True)
                _evi_min_w = _evi_min_r.read(1, window=((0, _min_height), (0, _min_width)), masked=True)
                _cur_band = _cur_r.read(1, window=((0, _min_height), (0, _min_width)), masked=True)
                _dst_f = np.zeros(_cur_band.shape)
                _newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.mask_or(np.ma.getmask(_cur_band), np.ma.getmask(_evi_min_w)),
                                                                         np.ma.getmask(_evi_max_w)),
                                            _dst_f)
#                evi_min_ma = np.ma.masked_where(np.ma.getmask(cur_band), evi_min_w)
                # newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(cur_band), np.ma.getmask(evi_max_a)),
                #                             dst_f)
                _numerator = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_cur_band), np.ma.getmask(_evi_min_w)),
                                            _dst_f)
                _numerator += (_cur_band - _evi_min_w)


                _profile.update(width=_min_width, height=_min_height)
                # with rasterio.open("c:\Prima\data\Temp\cur-min_evi.tif", 'w', **_profile) as _dst:
                #     _dst.write(_numerator.astype(rasterio.int16), 1)
                _denominator = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_evi_max_w), np.ma.getmask(_evi_min_w)),
                                            _dst_f)
                _denominator += (_evi_max_w - _evi_min_w)
                # with rasterio.open("c:\Prima\data\Temp\max-min_evi.tif", 'w', **_profile) as _dst:
                #     _dst.write(_denominator.astype(rasterio.int16), 1)
                with np.errstate(divide='ignore'):
                    _newd_f += (np.divide(_numerator, _denominator) * 100.0)
                _profile.update(dtype=rasterio.float64)
                # with rasterio.open("c:\Prima\data\Temp\division_evi.tif", 'w', **_profile) as _dst:
                #     _dst.write(_newd_f.astype(rasterio.float64), 1)
                _res = _newd_f.filled(fill_value=_cur_r.nodata)
                _res2 = np.ma.masked_where(_res == _cur_r.nodata, _res)

                with rasterio.open(dst_filename, 'w', **_profile) as _dst:
                    _dst.write(_res2.astype(rasterio.float64), 1)
    return None

def calc_VHI(vci_filename, tci_filename, dst_filename, resample='TCI'):
    # arcpy-free version
    # calculate Vegetation Health Index
    # VHI = 0.5 x (VCI + TCI)
    with rasterio.open(vci_filename) as _vci_r:
        _vci_a = _vci_r.read(1, masked=True)
        print 'vci no data {0}'.format(_vci_r.nodatavals)
        with rasterio.open(tci_filename) as _tci_r:
            _tci_a = _tci_r.read(1, masked=True)
            _profile = _tci_r.profile.copy()
            # check that resolution of vci matches resolution of tci
            _tci_aff = _tci_r.transform
            _vci_aff = _vci_r.transform
            print 'vci {0}, {1}'.format(_vci_aff, type(_vci_aff)) #.a, _vci_aff.e)
            print 'tci {0}, {1}'.format(_tci_aff, type(_tci_aff)) #.a, _tci_aff.e)
            # if _tci_aff.a != _vci_aff.a or _tci_aff.e != _vci_aff.e:
            #     if resample == 'TCI':
            #         # resample TCI to VCI resolution
            #         _newaff = rasterio.Affine(_tci_aff.a*(_vci_aff.a/_tci_aff.a), _tci_aff.b, _tci_aff.c,
            #                                   _tci_aff.d, _tci_aff.e*(_vci_aff.e/_tci_aff.e), _tci_aff.f)
            #         _newarr = np.empty(shape=(int((_tci_a.shape[0])/(_vci_aff.a/_tci_aff.a)),
            #                                   int((_tci_a.shape[1])/(_vci_aff.e/_tci_aff.e))))
            #         try:
            #             rasterio.warp.reproject(
            #                 _tci_a, _newarr,
            #                 src_transform=_tci_aff,
            #                 dst_transform=_newaff,
            #                 src_crs=_tci_r.crs,
            #                 dst_crs=_tci_r.crs,
            #                 resampling=rasterio.warp.Resampling.bilinear)
            #         except Exception, e:
            #             print "Error in reproject "

            print 'vci {0}'.format(_vci_a.shape)
            print 'tci {0}'.format(_tci_a.shape)
            print 'tci no data {0}'.format(_tci_r.nodatavals)
    #         if _vci_a.shape[0] > _tci_a.shape[0] or _vci_a.shape[1] > _tci_a.shape[1]:
    #             # resample vci
    #             _newarr = np.empty(shape=(_tci_a.shape[0], _tci_a.shape[1]))
    #             # adjust the new affine transform to the smaller cell size
    #             _aff = _vci_r.transform
    #             _newaff = rasterio.Affine(_aff.a / (float(_tci_a.shape[0]) / float(_vci_a.shape[0])), _aff.b, _aff.c,
    #                             _aff.d, _aff.e / (float(_tci_a.shape[1]) / float(_vci_a.shape[1])), _aff[5])
    #
    #             try:
    #                 rasterio.warp.reproject(
    #                     _vci_a, _newarr,
    #                     src_transform=_aff,
    #                     dst_transform=_newaff,
    #                     src_crs=_tci_r.crs,
    #                     dst_crs=_tci_r.crs,
    #                     resampling=rasterio.warp.Resampling.bilinear)
    #             except Exception, e:
    #                 print "Error in reproject "
    #             _vci_a = np.ma.masked_where(np.ma.getmask(_tci_a), _newarr)
    #             _profile.update(dtype=rasterio.float64, nodata=-9999)
    #             with rasterio.open("C:\PRIMA\\data\\Temp\\reprojectd.tif", 'w', **_profile) as _dst:
    #                 _dst.write(_newarr.astype(rasterio.float32), 1)
    #             with rasterio.open("C:\PRIMA\\data\\Temp\\reprojectd_masked.tif", 'w', **_profile) as _dst:
    #                 _dst.write(_vci_a.astype(rasterio.float64), 1)
    # #                rasterUtils.resampleRaster(vci_filename, tmp_filename, gdal_path, tci_a.shape[0], tci_a.shape[1])
    #         elif _tci_a.shape[0] > _vci_a.shape[0] or _tci_a.shape[1] > _tci_a.shape[1]:
    #             # resample tci
    #             _newarr = np.empty(shape=(_vci_a.shape[0], _vci_a.shape[1]))
    #             # adjust the new affine transform to the larger cell size
    #             _aff = _tci_a.transform
    #             _newaff = rasterio.Affine(_aff.a / (_vci_a.shape[0] / _tci_a.shape[0]), _aff.b, _aff.c,
    #                                      _aff.d, _aff.e / (_vci_a.shape[1] / _tci_a.shape[1]), _aff.f)
    #             try:
    #                 rasterio.warp.reproject(
    #                     _tci_a, _newarr,
    #                     src_transform=_aff,
    #                     dst_transform=_newaff,
    #                     src_crs=_tci_a.crs,
    #                     dst_crs=_tci_a.crs,
    #                     resample=rasterio.warp.Resampling.bilinear)
    #             except Exception, e:
    #                 print "Error in reproject "
    #             _tci_a = np.ma.masked_where(np.ma.getmask(_vci_a), _newarr)

            _dst_ff = np.ma.array((_vci_a, _tci_a)).sum(axis=0)
            _dst_ff = np.ma.multiply(_dst_ff, 0.5)
            _dst_ff = _dst_ff.filled(fill_value=_vci_r.nodata)

            # _dst_f = np.zeros(_vci_a.shape)
            # _newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_vci_a), np.ma.getmask(_tci_a)),
            #                             _dst_f)
            # _newd_f += ((_vci_a + _tci_a) * 0.5)
            # _res = _newd_f.filled(fill_value=_vci_r.nodata)
            # _res2 = np.ma.masked_where(_res == _vci_r.nodata, _res)
            _profile.update(dtype=rasterio.float64, nodata=_vci_r.nodata)
            with rasterio.open(dst_filename, 'w', **_profile) as _dst:
                _dst.write(_dst_ff.astype(rasterio.float64), 1)
    return None