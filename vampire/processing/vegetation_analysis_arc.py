import arcpy
import logging
logger = logging.getLogger(__name__)

def calc_TCI(cur_filename, lta_max_filename, lta_min_filename, dst_filename):
    # calculate Temperature Condition Index
    # TCI = 100 x (LST_max - LST)/(LST_max - LST_min)
    cur_Raster = arcpy.Raster(cur_filename)
    lta_max_Raster = arcpy.Raster(lta_max_filename)
    lta_min_Raster = arcpy.Raster(lta_min_filename)
    denominator = arcpy.sa.Minus(lta_max_Raster, lta_min_Raster)
    numerator = arcpy.sa.Minus(lta_max_Raster, cur_Raster)
    dst_f = arcpy.sa.Divide(numerator, denominator)
    dst = arcpy.sa.Times(dst_f, 100)
    dst.save(dst_filename)
    return None

def calc_VCI(cur_filename, evi_max_filename, evi_min_filename, dst_filename):
     # calculate Vegetation Condition Index
    # VCI = 100 x (EVI - EVI_min)/(EVI_max - EVI_min)
    cur_Raster = arcpy.Raster(cur_filename)
    evi_max_Raster = arcpy.Raster(evi_max_filename)
    evi_min_Raster = arcpy.Raster(evi_min_filename)
    cur_scaled = arcpy.sa.Times(cur_Raster, 0.0001)
    evi_max_scaled = arcpy.sa.Times(evi_max_Raster, 0.0001)
    evi_min_scaled = arcpy.sa.Times(evi_min_Raster, 0.0001)
    denominator = arcpy.sa.Minus(evi_max_scaled, evi_min_scaled)
    numerator = arcpy.sa.Minus(cur_scaled, evi_min_scaled)
    dst_f = arcpy.sa.Divide(numerator, denominator)
    dst = arcpy.sa.Times(dst_f, 100)
    dst.save(dst_filename)
    return None

def calc_VHI(vci_filename, tci_filename, dst_filename):
     # calculate Vegetation Health Index
    # VHI = 0.5 x (VCI + TCI)
    _cellsize = arcpy.env.cellSize
    arcpy.env.cellSize = "MINOF"
    vci_Raster = arcpy.Raster(vci_filename)
    tci_Raster = arcpy.Raster(tci_filename)
    dst_f = arcpy.sa.Plus(vci_Raster, tci_Raster)
    dst = arcpy.sa.Times(dst_f, 0.5)
    dst.save(dst_filename)
    arcpy.env.cellSize = _cellsize
    return None



