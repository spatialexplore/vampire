import arcpy
import os
import vampire.csv_utils
import csv

def reclassify_raster(raster, threshold, output_raster):
    in_true_constant = 1
    in_false_constant = 0
    where_clause = 'VALUE > {0}'.format(threshold)

#    # Execute Con
#    out_con = arcpy.sa.Con(in_conditional_raster=raster, in_true_raster_or_constant=in_true_constant,
#                           in_false_raster_or_constant=in_false_constant, where_clause=where_clause)
#    out_con.save(output_raster)
    out_ras = arcpy.sa.SetNull(in_conditional_raster=raster, in_false_raster_or_constant=1, where_clause=where_clause)
    out_ras.save(output_raster)
    return None

def multiply_by_mask(raster, mask, output_raster):
    out_ras = arcpy.sa.Times(raster, mask)
    out_ras.save(output_raster)
    return None

def shapefile_to_table(input, output):
    if os.path.splitext(output)[1] != '.dbf':
        _output = '{0}{1}'.format(os.path.splitext(os.path.basename(output))[0], '.dbf')
        _output_csv = '{0}{1}'.format(os.path.splitext(output)[0], '.csv')
    else:
        _output = os.path.basename(output)
        _output_csv = '{0}{1}'.format(os.path.splitext(output)[0], '.csv')
    arcpy.TableToTable_conversion(input, os.path.dirname(output), os.path.splitext(_output)[0])
    vampire.csv_utils.convert_dbf_to_csv(os.path.join(os.path.dirname(output), _output), _output_csv)
    return None

def intersect_boundaries(boundary_list, boundary_output):
    arcpy.Intersect_analysis(in_features=boundary_list, out_feature_class=boundary_output)
    return None
