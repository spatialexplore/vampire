
import rasterio
import numpy as np
import os

# calculate a rainfall anomaly surface as int(100 * (current rainfall/long-term average rainfall) )
def calc_rainfall_anomaly(cur_filename, lta_filename, dst_filename):
    with rasterio.open(cur_filename) as cur_r:
        _cur_band = cur_r.read(1, masked=True)
        _profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_filename) as lta_r:
            lta_a = lta_r.read(1, masked=True)
            _div_f = _cur_band / lta_a
            _div_f = _div_f * 100
            _res = _div_f.filled(fill_value=cur_r.nodata)
            dst_f = np.zeros(_cur_band.shape)
            newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_cur_band), np.ma.getmask(lta_r)), dst_f)
            newd_f += np.divide(_cur_band, lta_a) * 100.0
            newd_f.astype(int)
            res = newd_f.filled(fill_value=cur_r.nodata)
            res2 = np.ma.masked_where(res==cur_r.nodata, res)
            _profile.update(dtype=rasterio.int32)
            with rasterio.open(path=dst_filename, mode='w', **_profile) as dst:
                dst.write(_res.astype(rasterio.int32), 1)
    return None

def calc_standardized_precipitation_index(cur_filename, lta_filename, ltsd_filename, dst_filename):
    with rasterio.open(cur_filename) as cur_r:
        _cur_band = cur_r.read(1, masked=True)
        _profile = cur_r.profile.copy()
        print cur_r.nodatavals
        with rasterio.open(lta_filename) as lta_r:
            lta_a = lta_r.read(1, masked=True)
            with rasterio.open(ltsd_filename) as ltsd_r:
                ltsd_a = ltsd_r.read(1, masked=True)
                _sub_f = _cur_band - lta_a
                _dst_f = _sub_f / ltsd_a
                _res = _dst_f.filled(fill_value=cur_r.nodata)
                # dst_f = np.zeros(_cur_band.shape)
                # newd_f = np.ma.masked_where(np.ma.mask_or(np.ma.getmask(_cur_band), np.ma.getmask(lta_r)), dst_f)
                # newd_f += np.divide(np.subtract(_cur_band, lta_a), ltsd_a)
                # newd_f.astype(float)
                # res = newd_f.filled(fill_value=cur_r.nodata)
                # res2 = np.ma.masked_where(res==cur_r.nodata, res)
                _profile.update(dtype=rasterio.float32)
                with rasterio.open(path=dst_filename, mode='w', **_profile) as dst:
                    dst.write(_res.astype(rasterio.float32), 1)
    return None

# Find the last day with precipitation greater than threshold in the list of rasters
# returns a raster of number of days since last rain
def days_since_last_rain(raster_list, dslw_filename, dsld_filename, num_wet_days_filename, rainfall_accum_filename,
                         temp_dir, threshold=0.5, max_days=30):

    # reclassify rasters to wet or dry - >0.5 = 1 (wet), <0.5 = 0 (dry)
    _reclass_rasters = []
##    rasters_list = arcpy.ListRasters()
    _count = 0
    _new_ras = None
    for ras in raster_list:
        # only look at last 'max_days' rasters
        if _count < max_days:
            _new_ras = os.path.join(temp_dir, 'temp_wd{0}'.format(_count))
##            newras = os.path.join(temp_path, '{0}_wd{1}'.format(os.path.splitext(os.path.basename(ras))[0], output_filenames[1]))
#    ##        newras = temp_path + '/' + os.path.splitext(os.path.basename(ras))[0] + '_wd' + '.tif'
#            # check if file exists
#            if os.path.isfile(newras) == False:
            _reclassify_wet_day(ras, _new_ras, threshold)
            _reclass_rasters.append(_new_ras)
            _count += 1
        else:
            break
    print("successfully reclassified rasters")
    _reclass_rasters.sort(reverse=True)
    print(_reclass_rasters)

    # calculate last wet day
##    dslwfile = env.workspace + "/lwd/output/dslw25_29.tif"
#    dslwfile = os.path.join(output_path, '{0}_dslw{1}'.format(output_filenames[0], output_filenames[1]))
##    dsldfile = env.workspace + "/lwd/output/dsld25_29.tif"
#    dsldfile = os.path.join(output_path, '{0}_dsld{1}'.format(output_filenames[0], output_filenames[1]))
#    #lastWetDay(reclassRasters, outputfile, len(reclassRasters))
    _calc_num_days_since(rasters=_reclass_rasters, dslw_fn=dslw_filename, dsld_fn=dsld_filename, max_days=_count)
    print("successfully calculated last wet day")

    # calculate number of wet days
    _wet_days_total = None
    _profile = None
    with rasterio.open(_reclass_rasters[0]) as cur_r:
        _cur_band = cur_r.read(1, masked=True)
        _wet_days_total = np.zeros(shape=_cur_band.shape)
        _profile = cur_r.profile.copy()

    for ras in _reclass_rasters:
        with rasterio.open(ras) as cur_r:
            _cur_band = cur_r.read(1, masked=True)
            _wet_days_total = _wet_days_total + _cur_band
    _profile.update(dtype=rasterio.float32)
    with rasterio.open(path=num_wet_days_filename, mode='w', **_profile) as dst:
        dst.write(_wet_days_total.astype(rasterio.float32), 1)

#    cellStats = arcpy.sa.CellStatistics(_reclass_rasters, "SUM")
##    fname = os.path.join(output_path, '{0}_nwd{1}'.format(output_filenames[0], output_filenames[1]))
#    cellStats.save(num_wet_days_filename)

    # calculate total rainfall
    _ra_total = None
    _profile = None
    with rasterio.open(raster_list[0]) as cur_r:
        _cur_band = cur_r.read(1, masked=True)
        _ra_total = np.zeros(shape=_cur_band.shape)
        _profile = cur_r.profile.copy()

    for ras in raster_list:
        with rasterio.open(ras) as cur_r:
            _cur_band = cur_r.read(1, masked=True)
            _ra_total = _ra_total + _cur_band
    _profile.update(dtype=rasterio.float32)
    with rasterio.open(path=rainfall_accum_filename, mode='w', **_profile) as dst:
        dst.write(_ra_total.astype(rasterio.float32), 1)

# #    fname = os.path.join(output_path, '{0}_tot_precip{1}'.format(output_filenames[0], output_filenames[1]))
#    cellStats = arcpy.sa.CellStatistics(raster_list, "SUM")
#    cellStats.save(rainfall_accum_filename)
    return 0



# Reclassify raster to 1 if >= 0.5mm rainfall, 0 otherwise (wet days)
def _reclassify_wet_day(in_raster, out_raster, threshold):
#    arcpy.env.extent="MAXOF"
#    arcpy.env.cellSize="MAXOF"
#    ras = arcpy.sa.Raster(in_raster)
    with rasterio.open(in_raster) as cur_r:
        _cur_band = cur_r.read(1, masked=True)
        _out_ras = np.zeros(shape=_cur_band.shape)
        _profile = cur_r.profile.copy()
        _out_ras[_cur_band >= threshold] += 1
        _profile.update(dtype=rasterio.float32)
        with rasterio.open(path=out_raster, mode='w', **_profile) as dst:
            dst.write(_out_ras.astype(rasterio.float32), 1)

#    out_ras = arcpy.sa.Con(in_conditional_raster=in_raster,
#                           in_true_raster_or_constant=1,
#                           in_false_raster_or_constant=0,
#                           where_clause="VALUE >={0}".format(threshold))

##    ds = gdal.Open(in_raster)
##    ras_array = numpy.array(ds.GetRasterBand(1).ReadAsArray())
##    ras_array[ras_array == -9999] = numpy.nan
##    ras_array[ras_array < threshold] = 0
##    ras_array[ras_array >= threshold] = 1
##    out_ras = arcpy.NumPyArrayToRaster(ras_array, x_cell_size = ras.meanCellWidth,
##                                                 y_cell_size = ras.meanCellHeight)
#    out_ras.save(out_raster)
###    ras = arcpy.sa.Raster(in_raster)
###    ras.save("s:/WFP/MODIS/Scratch/rasout.tif")
####    out_con = arcpy.CopyRaster_management(ras, out_raster, "DEFAULTS", "", "-9999", "", "", "32_BIT_UNSIGNED")
####    out_con = arcpy.sa.Reclassify(out_con, "Value", arcpy.sa.RemapRange([[0.0, 0.5, 0], [0.5, 9999, 1]]) )
###    out_con = Con(Raster(in_raster) >= threshold, 1.0, 0.0)
####    out_con = Con(ras, 1, 0, "VALUE >= 0.5")
###    out_con.save(out_raster)
    return None



#calculate number of days since the last wet (dslw) or dry (dsld) day
# assumes input raster is 1 for wet and 0 for dry
# for example to calculate the number of days since last wet day, all days classified as "wet"
# will be 1 and the rest 0. Days with no data should be No Data
def _calc_num_days_since(rasters, dslw_fn, dsld_fn, max_days):
    _counter = 0
    # initialise masks - noDataMask is 1 where there is No Data across all rasters, 0 otherwise
    # since some regions will have No Data for some days, but valid data on other days. Need to
    # include these regions ALL the time.
    _no_data_mask = None
    _dry_mask = None
    _wet_mask = None
    _profile = None
    with rasterio.open(rasters[0]) as cur_r:
        _cur_band = cur_r.read(1, masked=False)
        _profile = cur_r.profile.copy()
        _no_data_mask = np.zeros(_cur_band.shape)
        _no_data_mask[_cur_band == cur_r.nodata] += 1
#    _no_data_mask = arcpy.sa.Con(arcpy.sa.IsNull(rasters[0]), 1, 0)
    # Highest Position provides position for all cell values - we need to mask out the dry cells
    # dryMask is 1 if rainfall is 0 (dry), and -999 if No Data
    # wetMask is 1 if rainfall is 1 (wet), and -999 if No Data
        _dry_mask = np.zeros(_cur_band.shape)
        _wet_mask = np.zeros(_cur_band.shape)
        _dry_mask[_cur_band<=0] += 1
        _wet_mask[_cur_band>0] += 1
        _dry_mask[_no_data_mask==1] = -999
        _wet_mask[_no_data_mask==1] = -999
#    _dry_mask = arcpy.sa.Con(rasters[0], 1, 0, "VALUE <= 0")
#    _wet_mask = arcpy.sa.BooleanNot(_dry_mask)
#    _dry_mask = arcpy.sa.Con(arcpy.sa.IsNull(_dry_mask), -999, _dry_mask)
#    _wet_mask = arcpy.sa.Con(arcpy.sa.IsNull(_wet_mask), -999, _wet_mask)

    #collect X=numDays consecutive rasters
    # rasters still contain NoData values
    _last_x_rasters = []
    _last_dry_rasters = []
    # make sure we have enough data
    if _counter+max_days > len(rasters):
        max_days = len(rasters)-_counter
    #
    for i in range(_counter,(_counter+max_days)):
        with rasterio.open(rasters[i]) as cur_r:
            _cur_band = cur_r.read(1, masked=False)
        # create NoData mask where *all* rasters have NoData
            _no_data = np.zeros(_cur_band.shape)
            _no_data[_cur_band==cur_r.nodata] = 1
            _no_data_mask = np.logical_and(_no_data_mask, _no_data)
#        _no_data_mask = arcpy.sa.BooleanAnd(_no_data_mask, arcpy.sa.Con(arcpy.sa.IsNull(rasters[i]), 1, 0))
        # temporarily set No Data values to -999 so the grid cell isn't ignored
        # in calculations
            _temp_raster = np.zeros(_cur_band.shape)
            _temp_raster[_cur_band == cur_r.nodata] = -999
            _temp_raster[_cur_band != cur_r.nodata] = _cur_band
#        _temp_raster = arcpy.sa.Con(arcpy.sa.IsNull(rasters[i]), -999, rasters[i])
        # _dry_mask is 1 if dry day (<0.5mm rain) OR No Data
            _dry = np.zeros(_cur_band.shape)
            _dry[_temp_raster <= 0] = 1
            _dry_mask = np.logical_and(_dry_mask, _dry)
#        _dry_mask = arcpy.sa.BooleanAnd(_dry_mask, arcpy.sa.Con(_temp_raster, 1, 0, "VALUE <= 0"))
        # _wet_mask is 1 if wet day (> threshold) OR No Data
            _wet = np.zeros(_cur_band.shape)
            _wet[_temp_raster != 0] = 1
            _wet_mask = np.logical_and(_wet_mask, _wet)
#        _wet_mask = arcpy.sa.BooleanAnd(_wet_mask, arcpy.sa.Con(_temp_raster, 1, 0, "VALUE <> 0"))
        # raster[i] is 1 if wet, 0 if dry. inverseRaster = 0 if wet, 1 if dry
            _inverse_raster = np.logical_not(_cur_band)
#        _inverse_raster = arcpy.sa.BooleanNot(rasters[i])
        #remove NoData (set to 0)
            _cur_band[_cur_band == cur_r.nodata] = 0
#        rasters[i] = arcpy.sa.Con(arcpy.sa.IsNull(rasters[i]), 0, rasters[i])
            _inverse_raster[_inverse_raster == cur_r.nodata] = 0
#        _inverse_raster = arcpy.sa.Con(arcpy.sa.IsNull(_inverse_raster), 0, _inverse_raster)

            _last_x_rasters.append(_cur_band)
            _last_dry_rasters.append(_inverse_raster)

    # create raster with number of days since last rain
    _dslw_stack = np.dstack(_last_x_rasters)
    _last_dry_stack = np.dstack(_last_dry_rasters)
    _days_since_last_wet = np.argmax(_dslw_stack, axis=2)
    _days_since_last_dry = np.argmax(_last_dry_stack, axis=2)
#    _days_since_last_wet = arcpy.sa.HighestPosition(_last_x_rasters)
#    _days_since_last_dry = arcpy.sa.HighestPosition(_last_dry_rasters)
##    daysSinceLastDry.save(env.workspace + "/lwd/output/dsld.tif")

##    noDataMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/noDataMask.tif")
    _dry_mask[_dry_mask == cur_r.nodata] = -999
    _wet_mask[_wet_mask == cur_r.nodata] = -999
#    _dry_mask = arcpy.sa.Con(arcpy.sa.IsNull(_dry_mask), -999, _dry_mask)
#    _wet_mask = arcpy.sa.Con(arcpy.sa.IsNull(_wet_mask), -999, _wet_mask)
##    wetMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/wetMask.tif")
##    dryMask.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/dryMask.tif")
##    outHighestPosition.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/hp.tif")
    # reset NoData
    _dslw = np.copy(_days_since_last_wet)
    _dslw[_no_data_mask >=1] = cur_r.nodata
    _dsld = np.copy(_days_since_last_dry)
    _dsld[_no_data_mask >=1] = cur_r.nodata

    _dslw[_dry_mask >=1] = -999
    _dsld[_wet_mask >=1] = -999

#    outFinal = arcpy.sa.SetNull(_no_data_mask, _days_since_last_wet, "VALUE >= 1")
#    outFinal3 = arcpy.sa.SetNull(_no_data_mask, _days_since_last_dry, "VALUE >= 1")
##    outFinal.save(env.workspace + "/lwd/output/outdslw.tif")
##    outFinal3.save(env.workspace + "/lwd/output/outdsld.tif")

#    outFinal2 = arcpy.sa.Con(_dry_mask, -999, outFinal, "VALUE >= 1")
#    outFinal4 = arcpy.sa.Con(_wet_mask, -999, outFinal3, "VALUE >= 1")

    # Save the output
    _profile.update(dtype=rasterio.float32)
    with rasterio.open(path=dslw_fn, mode='w', **_profile) as dst:
        dst.write(_dslw.astype(rasterio.float32), 1)
    with rasterio.open(path=dsld_fn, mode='w', **_profile) as dst2:
        dst2.write(_dsld.astype(rasterio.float32), 1)
#    outFinal2.save(dslw_fn)
#    outFinal4.save(dsld_fn)
    return 0
