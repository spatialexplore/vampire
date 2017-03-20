
import rasterio
import numpy as np

# calculate a rainfall anomaly surface as int(100 * (current rainfall/long-term average rainfall) )
def calc_rainfall_anomaly(cur_filename, lta_filename, dst_filename):
    with rasterio.open(cur_filename) as cur_r:
        _cur_band = cur_r.read(1, masked=True)
        _profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_filename) as lta_r:
            lta_a = lta_r.read(1, masked=True)
            dst_f = np.zeros(_cur_band.shape)
            newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_cur_band), np.ma.getmask(lta_r)), dst_f)
            newd_f += np.divide(_cur_band, lta_a) * 100.0
            newd_f.astype(int)
            res = newd_f.filled(fill_value=cur_r.nodata)
            res2 = np.ma.masked_where(res==cur_r.nodata, res)
            _profile.update(dtype=rasterio.int32)
            with rasterio.open(path=dst_filename, mode='w', **_profile) as dst:
                dst.write(res2.astype(rasterio.int32), 1)
    return None
