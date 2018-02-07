
import os
import arcpy
import gdal
import numpy
import logging
logger = logging.getLogger(__name__)

# Check out the ArcGIS Spatial Analyst extension license
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddMessage("Error: Couldn't get Spatial Analyst extenstion")
arcpy.env.overwriteOutput = 1

# calculate a rainfall anomaly surface as int(100 * (current rainfall/long-term average rainfall) )
def calc_rainfall_anomaly(cur_filename, lta_filename, dst_filename):
    _cur_raster = arcpy.sa.Raster(cur_filename)
    _lta_raster = arcpy.sa.Raster(lta_filename)
    dst_f = arcpy.sa.Divide(_cur_raster, _lta_raster)
    dst_100f = arcpy.sa.Times(dst_f, 100)
    dst = arcpy.sa.Int(dst_100f)
    dst.save(dst_filename)
    return None

def calc_standardized_precipitation_index(cur_filename, lta_filename, ltsd_filename, dst_filename):
    _cur_raster = arcpy.sa.Raster(cur_filename)
    _lta_raster = arcpy.sa.Raster(lta_filename)
    _ltsd_raster = arcpy.sa.Raster(ltsd_filename)
    dst_f = arcpy.sa.Divide(arcpy.sa.Minus(_cur_raster, _lta_raster), _ltsd_raster)
    dst = arcpy.sa.Float(dst_f)
    dst.save(dst_filename)
    return None

# calculate a drought index based on rainfall anomaly for the areas provided in the shapefile.
# where rainfall anomaly is < rainfall_anomaly_threshold, it is also checked against precipitation
# to ensure there is also < precipitation_threshold of rainfall during the interval.
def calc_drought_index(ra_filename, cur_filename, shp_filename, dst_filename, ra_threshold, pr_threshold):

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
            _new_ras = os.path.join(temp_dir, 'temp_wd{0:0>2}'.format(_count))
##            newras = os.path.join(temp_path, '{0}_wd{1}'.format(os.path.splitext(os.path.basename(ras))[0], output_filenames[1]))
#    ##        newras = temp_path + '/' + os.path.splitext(os.path.basename(ras))[0] + '_wd' + '.tif'
#            # check if file exists
#            if os.path.isfile(newras) == False:
            _reclassify_wet_day(ras, _new_ras, threshold)
            _reclass_rasters.append(_new_ras)
            _count += 1
        else:
            break
    logger.debug("successfully reclassified rasters")
    _reclass_rasters.sort(reverse=True)
    logger.debug(_reclass_rasters)

    # calculate last wet day
##    dslwfile = env.workspace + "/lwd/output/dslw25_29.tif"
#    dslwfile = os.path.join(output_path, '{0}_dslw{1}'.format(output_filenames[0], output_filenames[1]))
##    dsldfile = env.workspace + "/lwd/output/dsld25_29.tif"
#    dsldfile = os.path.join(output_path, '{0}_dsld{1}'.format(output_filenames[0], output_filenames[1]))
#    #lastWetDay(reclassRasters, outputfile, len(reclassRasters))
    _calc_num_days_since(rasters=_reclass_rasters, dslw_fn=dslw_filename, dsld_fn=dsld_filename, max_days=_count)
    logger.debug("successfully calculated last wet day")

    # calculate number of wet days
    cellStats = arcpy.sa.CellStatistics(_reclass_rasters, "SUM")
#    fname = os.path.join(output_path, '{0}_nwd{1}'.format(output_filenames[0], output_filenames[1]))
    cellStats.save(num_wet_days_filename)
    # calculate total rainfall
#    fname = os.path.join(output_path, '{0}_tot_precip{1}'.format(output_filenames[0], output_filenames[1]))
    cellStats = arcpy.sa.CellStatistics(raster_list, "SUM")
    cellStats.save(rainfall_accum_filename)
    return 0



# Reclassify raster to 1 if >= 0.5mm rainfall, 0 otherwise (wet days)
def _reclassify_wet_day(in_raster, out_raster, threshold):
    _extent = arcpy.env.extent
    _cellsize = arcpy.env.cellSize
    arcpy.env.extent="MAXOF"
    arcpy.env.cellSize="MAXOF"
    ras = arcpy.sa.Raster(in_raster)
    out_ras = arcpy.sa.Con(in_conditional_raster=in_raster,
                           in_true_raster_or_constant=1,
                           in_false_raster_or_constant=0,
                           where_clause="VALUE >{0}".format(int(threshold)))
#                           where_clause="VALUE >={0}".format(threshold))

#    ds = gdal.Open(in_raster)
#    ras_array = numpy.array(ds.GetRasterBand(1).ReadAsArray())
#    ras_array[ras_array == -9999] = numpy.nan
#    ras_array[ras_array < threshold] = 0
#    ras_array[ras_array >= threshold] = 1
#    out_ras = arcpy.NumPyArrayToRaster(ras_array, x_cell_size = ras.meanCellWidth,
#                                                 y_cell_size = ras.meanCellHeight)
    out_ras.save(out_raster)
##    ras = arcpy.sa.Raster(in_raster)
##    ras.save("s:/WFP/MODIS/Scratch/rasout.tif")
###    out_con = arcpy.CopyRaster_management(ras, out_raster, "DEFAULTS", "", "-9999", "", "", "32_BIT_UNSIGNED")
###    out_con = arcpy.sa.Reclassify(out_con, "Value", arcpy.sa.RemapRange([[0.0, 0.5, 0], [0.5, 9999, 1]]) )
##    out_con = Con(Raster(in_raster) >= threshold, 1.0, 0.0)
###    out_con = Con(ras, 1, 0, "VALUE >= 0.5")
##    out_con.save(out_raster)
    arcpy.env.cellSize = _cellsize
    arcpy.env.extent = _extent
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
    _no_data_mask = arcpy.sa.Con(arcpy.sa.IsNull(rasters[0]), 1, 0)
    # Highest Position provides position for all cell values - we need to mask out the dry cells
    # dryMask is 1 if rainfall is 0 (dry), and -999 if No Data
    # wetMask is 1 if rainfall is 1 (wet), and -999 if No Data
    _dry_mask = arcpy.sa.Con(rasters[0], 1, 0, "VALUE <= 0")
    _wet_mask = arcpy.sa.BooleanNot(_dry_mask)
    _dry_mask = arcpy.sa.Con(arcpy.sa.IsNull(_dry_mask), -999, _dry_mask)
    _wet_mask = arcpy.sa.Con(arcpy.sa.IsNull(_wet_mask), -999, _wet_mask)

    #collect X=numDays consecutive rasters
    # rasters still contain NoData values
    _last_x_rasters = []
    _last_dry_rasters = []
    # make sure we have enough data
    if _counter+max_days > len(rasters):
        max_days = len(rasters)-_counter
    #
    for i in range(_counter,(_counter+max_days)):
        # create NoData mask where *all* rasters have NoData
        _no_data_mask = arcpy.sa.BooleanAnd(_no_data_mask, arcpy.sa.Con(arcpy.sa.IsNull(rasters[i]), 1, 0))
        # temporarily set No Data values to -999 so the grid cell isn't ignored
        # in calculations
        _temp_raster = arcpy.sa.Con(arcpy.sa.IsNull(rasters[i]), -999, rasters[i])
        # _dry_mask is 1 if dry day (<0.5mm rain) OR No Data
        _dry_mask = arcpy.sa.BooleanAnd(_dry_mask, arcpy.sa.Con(_temp_raster, 1, 0, "VALUE <= 0"))
        # _wet_mask is 1 if wet day (> threshold) OR No Data
        _wet_mask = arcpy.sa.BooleanAnd(_wet_mask, arcpy.sa.Con(_temp_raster, 1, 0, "VALUE <> 0"))
        # raster[i] is 1 if wet, 0 if dry. inverseRaster = 0 if wet, 1 if dry
        _inverse_raster = arcpy.sa.BooleanNot(rasters[i])
        #remove NoData (set to 0)
### temporarily remove this
#        rasters[i] = arcpy.sa.Con(arcpy.sa.IsNull(rasters[i]), 0, rasters[i])
        _inverse_raster = arcpy.sa.Con(arcpy.sa.IsNull(_inverse_raster), 0, _inverse_raster)
        _last_x_rasters.append(rasters[i])
        _last_dry_rasters.append(_inverse_raster)

    # create raster with number of days since last rain
    _highest_position_wet = arcpy.sa.HighestPosition(_last_x_rasters)
    _highest_position_dry = arcpy.sa.HighestPosition(_last_dry_rasters)

    _days_since_last_wet = _highest_position_wet - 1
    _days_since_last_dry = _highest_position_dry - 1

#    _days_since_last_dry.save("S:\\WFP2\\PRISM\\data\\Temp\\dsld.tif")
#    _days_since_last_wet.save("S:\\WFP2\\PRISM\\data\\Temp\\dslw.tif")

#    _no_data_mask.save("S:\\WFP2\\PRISM\\data\\Temp\\noDataMask.tif")
    _dry_mask = arcpy.sa.Con(arcpy.sa.IsNull(_dry_mask), -999, _dry_mask)
    _wet_mask = arcpy.sa.Con(arcpy.sa.IsNull(_wet_mask), -999, _wet_mask)
#    _wet_mask.save("S:\\WFP2\\PRISM\\data\\Temp\\wetMask.tif")
#    _dry_mask.save("S:\\WFP2\\PRISM\\data\\Temp\\dryMask.tif")
#    outHighestPosition.save("S:/WFP/CHIRPS/Daily/2015/p25/lwd/hp.tif")
    # reset NoData
    _dslw_no_data = arcpy.sa.SetNull(_no_data_mask, _days_since_last_wet, "VALUE >= 1")
    _dsld_no_data = arcpy.sa.SetNull(_no_data_mask, _days_since_last_dry, "VALUE >= 1")
#    outFinal.save(env.workspace + "/lwd/output/outdslw.tif")
#    outFinal3.save(env.workspace + "/lwd/output/outdsld.tif")
    _dslw_output = arcpy.sa.Con(_dry_mask, -999, _dslw_no_data, "VALUE >= 1")
    _dsld_output = arcpy.sa.Con(_wet_mask, -999, _dsld_no_data, "VALUE >= 1")

    # Save the output
    arcpy.SetRasterProperties_management(_dsld_output, nodata="1 -999")
    arcpy.SetRasterProperties_management(_dslw_output, nodata="1 -999")
    _dslw_output.save(dslw_fn)
    _dsld_output.save(dsld_fn)
    return 0

def calc_flood_alert(forecast_filename, threshold_filename, dst_filename, value=1):
    _forecast_raster = arcpy.sa.Raster(forecast_filename)
    _threshold_raster = arcpy.sa.Raster(threshold_filename)
    _cellsize = arcpy.env.cellSize
    arcpy.env.cellSize = "MINOF"
    dst = arcpy.sa.GreaterThanEqual(_forecast_raster, _threshold_raster) * int(value)
    # if value != 1:
    #     dst2 = arcpy.sa.Times(dst, value)
    #     dst = dst2
    dst.save(dst_filename)
    arcpy.env.cellSize = _cellsize
    return 0