import time
import configArcGIS as config
import arcpy
import arceditor
import sys
import os
import logging

LOG_FILENAME = 'vampire_log.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
#local variable
date = time.strftime('%c')
product = config.config['product']
proj = config.config['proj']
country = config.config['country']
datafolder = config.config['sourcedata']+'\\'+country
file_path = config.config['gdbpath']
gdbdir = file_path+'\\'+country
storingConfig = config.config['storingConfig']


def createMosaicDataset(gdb, MosDatasetName):
    arcpy.CreateMosaicDataset_management(gdb, MosDatasetName,
                                         "PROJCS['WGS_1984_UTM_Zone_49S',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',10000000.0],PARAMETER['Central_Meridian',111.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]];-5120900 1900 10000;-100000 10000;-100000 10000;0,001;0,001;0,001;IsHighPrecision",
                                         "", "", "NONE", "")

def addRastertoMDS(MDS, folder):
    arcpy.AddRastersToMosaicDataset_management(MDS, "Raster Dataset",folder,
                                               "UPDATE_CELL_SIZES", "UPDATE_BOUNDARY", "NO_OVERVIEWS", "", "0", "1500",
                                               "", "", "SUBFOLDERS", "OVERWRITE_DUPLICATES", "NO_PYRAMIDS", "NO_STATISTICS",
                                               "NO_THUMBNAILS", "", "NO_FORCE_SPATIAL_REFERENCE")
def update_mosaic_statistics (mosaic_dataset):
    logging.debug('updating mosaic statistics')
    arcpy.management.CalculateStatistics(mosaic_dataset)
    arcpy.management.BuildPyramidsandStatistics(mosaic_dataset, 'INCLUDE_SUBDIRECTORIES', 'BUILD_PYRAMIDS', 'CALCULATE_STATISTICS')
    arcpy.RefreshCatalog(mosaic_dataset)

try:

    if storingConfig == 'file':
        logging.debug(date +": we are using file geodatabase")
        for x in product:
            gdbname = gdbdir+'\\'+x+'.gdb'
            MDS = gdbname + '\\' + x
            if arcpy.Exists(MDS):
                print("Mosaic dataset "+MDS+" already exist")
            else:
                createMosaicDataset(gdbname, x)
                logging.debug(date +": Mosaic Dataset " + gdbname + " is created")
            workspace = datafolder + "/" + x
            addRastertoMDS(MDS, workspace)
            update_mosaic_statistics(MDS)
    elif storingConfig == 'ent':
        logging.debug(date +"we are using enterprise geodatabase")
        for x in product:
            egdbname = country.lower() + '_' + x
            gdb = "Database Connections/"+egdbname+".sde"
            MDS = gdb + '/' + egdbname + ".sde." + egdbname
            if arcpy.Exists(MDS):
                print("Mosaic dataset "+MDS+" already exist")
            else:
                createMosaicDataset(gdb,egdbname)
                logging.debug(date +": Mosaic Dataset "+egdbname+" is created")

            #print(MDS)
            workspace = datafolder + "/" + x
            addRastertoMDS(MDS, workspace)
            update_mosaic_statistics(MDS)
except Exception:
    e = sys.exc_info()[1]
    logging.debug(date +": "+e.args[0])
    print(e.args[0])
