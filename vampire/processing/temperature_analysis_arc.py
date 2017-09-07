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

# calculate a Temperature Condition Index (TCI) surface as
# int(100 x (LST long-term maximum - current LST)/(LST long-term maximum - LST long-term minimum))
def calc_TCI(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)
    _cur_raster = arcpy.Raster(cur_filename)
    _lta_max_raster = arcpy.Raster(lta_max_filename)
    _lta_min_raster = arcpy.Raster(lta_min_filename)
    _denominator = arcpy.sa.Minus(_lta_max_raster, _lta_min_raster)
    _numerator = arcpy.sa.Minus(_lta_max_raster, _cur_raster)
    _dst_f = arcpy.sa.Divide(_numerator, _denominator)
    _dst = arcpy.sa.Times(_dst_f, 100)
    _dst.save(dst_filename)
    return None
