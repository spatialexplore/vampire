import rasterio
import numpy as np
import logging
logger = logging.getLogger(__name__)

def calc_TCI(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    # calculate Temperature Condition Index
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)

    with rasterio.open(cur_filename) as cur_r:
        cur_band = cur_r.read(1, masked=True)
        profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_max_filename) as lta_max_r:
            lta_max_a = lta_max_r.read(1, masked=True)
            with rasterio.open(lta_min_filename) as lta_min_r:
                lta_min_a = lta_min_r.read(1, masked=True)
                _numerator = lta_max_a - cur_band
                _denominator = lta_max_a - lta_min_a
                _tci = _numerator /_denominator
                _tci = _tci*100.0
                _res = _tci.filled(fill_value=cur_r.nodata)
                profile.update(dtype=rasterio.float32)
                with rasterio.open(dst_filename, 'w', **profile) as dst:
                    dst.write(_res.astype(rasterio.float32), 1)

                # dst_f = np.zeros(cur_band.shape)
                # newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(cur_band), np.ma.getmask(lta_max_a)),
                #                             dst_f)
                # numerator=(lta_max_a - cur_band)
                # denominator = (lta_max_a - lta_min_a)
                # newd_f += (np.divide(numerator, denominator) * 100.0)
                #
                # res = newd_f.filled(fill_value=cur_r.nodata)
                # res2 = np.ma.masked_where(res == cur_r.nodata, res)
                #
                # profile.update(dtype=rasterio.float64)
                # with rasterio.open(dst_filename, 'w', **profile) as dst:
                #     dst.write(res2.astype(rasterio.float64), 1)
    return None
