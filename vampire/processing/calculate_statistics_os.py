
import rasterio
import numpy as np

def calc_average(file_list, avg_file):
#    print "calcAverage: ", file_list
    if file_list:
        arrayList = []
        first = True
        profile = None
        for f in file_list:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.dstack(arrayList)
        dst_r = np.mean(dst_a, axis=2)
        with rasterio.open(avg_file, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float32), 1)
    return None

def calc_min(file_list, min_file):
    print "calcMin (open source version): ", file_list
    if file_list:
        arrayList = []
        first = True
        profile = None
        for f in file_list:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.dstack(arrayList)
        dst_r = np.amin(dst_a, axis=2)
        with rasterio.open(min_file, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float32), 1)
            print "saved minimum in: ", min_file
    return None

def calc_max(file_list, max_file):
#    print "calc_max (open source version): ", file_list
    if file_list:
        arrayList = []
        first = True
        profile = None
        for f in file_list:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.dstack(arrayList)
        dst_r = np.amax(dst_a, axis=2)
        with rasterio.open(max_file, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float32), 1)
#            print "saved maximum in: ", max_file
    return None

def calc_std_dev(file_list, sd_file):
#    print "calcStDev (open source version): ", file_list
    if file_list:
        arrayList = []
        first = True
        profile = None
        for f in file_list:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.dstack(arrayList)
        dst_r = np.std(dst_a, axis=2, ddof=1)
        with rasterio.open(sd_file, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float32), 1)
#            print "saved standard deviation in: ", sd_file
    return None

def calc_sum(file_list, sum_file):
    print "calcSum (open source version): ", file_list
    if file_list:
        arrayList = []
        first = True
        profile = None
        for f in file_list:
            with rasterio.open(f) as cur_r:
                if first:
                    profile = cur_r.profile.copy()
                    first = False
                cur_a = cur_r.read(1, masked=True)
                arrayList.append(cur_a)
        dst_a = np.dstack(arrayList)
        dst_r = np.sum(dst_a, axis=2, ddof=1)
        with rasterio.open(sum_file, 'w', **profile) as dst:
            dst.write(dst_r.astype(rasterio.float32), 1)
            print "saved sum in: ", sum_file
    return None

def calc_average_of_day_night(day_file, night_file, avg_file):
    print "calcAverage: ", day_file, night_file
    with rasterio.open(day_file) as day_r:
        profile = day_r.profile.copy()
#        profile.update(dtype=rasterio.uint32)
        day_a = day_r.read(1, masked=True)
        with rasterio.open(night_file) as night_r:
            night_a = night_r.read(1, masked=True)
            dst_r = np.mean((day_a, night_a), axis=0)
            with rasterio.open(avg_file, 'w', **profile) as dst:
                dst.write(dst_r.astype(rasterio.uint16), 1)
    return None