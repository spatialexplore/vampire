import arcpy
import dbfpy.dbf
import csv
import os
import vampire.csv_utils
import logging
logger = logging.getLogger(__name__)

def calc_average(file_list, avg_file):
    """ Calculate pixel-by-pixel average of a list of rasters and save result as new raster. 
    
    For each pixel, calculate the average of values in the list of rasters. Uses ArcPy
    CellStatistics function. Requires an ArcGIS SpatialAnalyst licence.

    Parameters
    ----------
    file_list : list
        List of raster files
    avg_file : str
        Filename of output file

    Returns
    -------
    None
        Returns None

    """
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "MEAN")
    # Save the output
    outRaster.save(avg_file)
#    print "saved avg in: ", avg_file
    return None

def calc_min(file_list, min_file):
    """ Calculate pixel-by-pixel minimum of a list of rasters and save result as new raster. 
    
    For each pixel, calculate the minimum of values in the list of rasters. Uses ArcPy
    CellStatistics function. Requires an ArcGIS SpatialAnalyst licence.
    
    Parameters
    ----------
    file_list : list
        List of raster files
    min_file : str
        Filename of output file
    
    Returns
    -------
    None
        Returns None
    
    """
    #    print "calcMin: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "MINIMUM")
    # Save the output
    outRaster.save(min_file)
#    print "saved minimum in: ", min_file
    return None

def calc_max(file_list, max_file):
    """ Calculate pixel-by-pixel maximum of a list of rasters and save result as new raster. 
    
    For each pixel, calculate the maximum of values in the list of rasters. Uses ArcPy
    CellStatistics function. Requires an ArcGIS SpatialAnalyst licence.
    
    Parameters
    ----------
    file_list : list
        List of raster files
    max_file : str
        Filename of output file
    
    Returns
    -------
    None
        Returns None
    
    """
    #    print "calcAverage: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "MAXIMUM")
    # Save the output
    outRaster.save(max_file)
#    print "saved maximum in: ", max_file
    return None

def calc_std_dev(file_list, sd_file):
    """ Calculate pixel-by-pixel standard deviation of a list of rasters and save result as new raster. 
    
    For each pixel, calculate the standard deviation of values in the list of rasters. Uses ArcPy
    CellStatistics function. Requires an ArcGIS SpatialAnalyst licence.
    
    Parameters
    ----------
    file_list : list
        List of raster files
    sd_file : str
        Filename of output file
    
    Returns
    -------
    None
        Returns None
    
    """
    #    print "calcStDev: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "STD")
    # Save the output
    outRaster.save(sd_file)
#    print "saved standard deviation in: ", sd_file
    return None

def calc_sum(file_list, sum_file):
    """ Calculate pixel-by-pixel sum of a list of rasters and save result as new raster. 
    
    For each pixel, calculate the sum of values in the list of rasters. Uses ArcPy
    CellStatistics function. Requires an ArcGIS SpatialAnalyst licence.
    
    Parameters
    ----------
    file_list : list
        List of raster files
    sum_file : str
        Filename of output file
    
    Returns
    -------
    None
        Returns None
    
    """
    #    print "calcSum: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "SUM")
    # Save the output
    outRaster.save(sum_file)
#    print "saved sum in: ", sum_file
    return None

def calc_average_of_day_night(day_file, night_file, avg_file):
    """ Calculate pixel-by-pixel average of land surface temperature day and night rasters and save result as new raster. 

    For each pixel, calculate the mean of values in the two rasters. Uses ArcPy
    CellStatistics function. Requires an ArcGIS SpatialAnalyst licence.

    Parameters
    ----------
    day_file : str
        Filename of day file
    night_file : str
        Filename of night file
    avg_file : str
        Filename of output file

    Returns
    -------
    None
        Returns None

    """
    print "calcAverage: ", day_file, night_file
    #an empty array/vector in which to store the different bands
    rasters = []
    #open rasters
    rasters.append(day_file)
    rasters.append(night_file)
    outRaster = arcpy.sa.CellStatistics(rasters, "MEAN", "DATA")
    # Save the output
    outRaster.save(avg_file)
    print "saved avg in: ", avg_file
    return None

def calc_zonal_statistics(raster_file, polygon_file, zone_field, output_table):
    """ Calculate zonal statistics for a raster and vector and save result as .dbf and .csv files. 

    For each polygon in the vector file, calculate set of statistics from the raster (sum, mean, max, min, count). 
    Uses ArcPy ZonalStatisticsAsTable function. Requires an ArcGIS SpatialAnalyst licence.

    Parameters
    ----------
    raster_file : str
        Filename of raster file
    polygon_file : str
        Filename of vector file
    zone_field : str
        Name of field labelling the zones within vector file
    output_table : str
        Filename of output table (.dbf or .csv)

    Returns
    -------
    None
        Returns None

    """
    arcpy.CheckOutExtension("Spatial")
    arcpy.MakeFeatureLayer_management(polygon_file, "layer")
    layer = arcpy.mapping.Layer("layer")
    # First calculate statistics on raster.
    arcpy.CalculateStatistics_management(in_raster_dataset=raster_file)
    # set up .dbf and .csv filenames
    if output_table.endswith('.dbf'):
        _output_csv = os.path.splitext(output_table)[0]
        _output_csv = '{0}.csv'.format(_output_csv)
        _output_dbf = output_table
    elif output_table.endswith('.csv'):
        _output_dbf = os.path.splitext(output_table)[0]
        _output_dbf = '{0}.dbf'.format(_output_dbf)
        _output_csv = output_table
    else:
        _output_dbf = '{0}.dbf'.format(output_table)
        _output_csv = '{0}.csv'.format(output_table)
    _output_dbf = '{0}.dbf'.format(os.path.splitext(os.path.basename(raster_file))[0])
    if len(_output_dbf) > 12:
        _output_dbf = 'temp_output.dbf'
    arcpy.env.workspace = os.path.dirname(raster_file)
    _output_filename = os.path.basename(_output_dbf)
    # now calculate zonal statistics as table
    arcpy.sa.ZonalStatisticsAsTable(in_zone_data=layer, zone_field=zone_field,
                                    in_value_raster=raster_file,out_table=_output_dbf,
                                    ignore_nodata="DATA", statistics_type="ALL")
    if arcpy.Exists(layer):
        arcpy.Delete_management(layer)
    # convert to .csv
    vampire.csv_utils.convert_dbf_to_csv(os.path.join(os.path.dirname(raster_file), _output_dbf), _output_csv)

    return None

def mosaic_rasters(raster_file_list, output_dir, output_file, mosaic_method):
    """ Mosaic the list of files using the specified method and save to output_file.

    Parameters
    ----------
    raster_file : str
        Filename of raster file
    polygon_file : str
        Filename of vector file
    zone_field : str
        Name of field labelling the zones within vector file
    output_table : str
        Filename of output table (.dbf or .csv)

    Returns
    -------
    None
        Returns None

    """
    arcpy.CheckOutExtension("Spatial")
    arcpy.MosaicToNewRaster_management(input_rasters=raster_file_list, output_location=output_dir,
                                       raster_dataset_name_with_extension=output_file, mosaic_method=mosaic_method,
                                       number_of_bands=1)
    return None