import arcpy
import os
import vampire.csv_utils
import calculate_statistics_arc as calculate_statistics
import csv
import geopandas
import pandas
import logging
logger = logging.getLogger(__name__)

def calculate_crop_impact(hazard_raster, threshold, hazard_var,
                          crop_boundary, crop_field,
                          admin_boundary, admin_field,
                          output_file,
                          start_date, end_date, intersect=False):
    _output_dir = os.path.dirname(output_file)
    # reclassify hazard raster to generate mask of all <= threshold
    _reclass_raster = os.path.join(os.path.dirname(output_file), 'hazard_crops_reclass.tif')
    reclassify_raster(raster=hazard_raster, threshold=threshold, output_raster=_reclass_raster)

    _zone_table = os.path.join(_output_dir, 'hazard_crops_table.csv')

    # calculate impact on boundary
    # if have admin boundary as well, intersect the two boundaries first, then dissolve after the join to
    # calculate crop impact per admin area
    if admin_boundary is None:
        _boundary = crop_boundary
        _zone_field = crop_field
    else:
        if intersect:
            _boundary_output = os.path.join(_output_dir, 'crop_admin_intersection.shp')
            intersect_boundaries([crop_boundary, admin_boundary], _boundary_output)
            _boundary = _boundary_output
            _zone_field = 'fid'
        else:
            _boundary = crop_boundary
            _zone_field = 'fid'
    stats = calculate_statistics.calc_zonal_statistics(raster_file=_reclass_raster, polygon_file=_boundary,
                                                       zone_field=_zone_field, output_table=_zone_table)

    # convert to hectares
    # TODO: get multiplier from defaults depending on resolution of hazard raster
    vampire.csv_utils.calc_field(table_name=_zone_table, new_field='area_aff', cal_field='COUNT', multiplier=6.25)
    # add start and end date fields and set values
    vampire.csv_utils.add_field(table_name=_zone_table, new_field='start_date', value=start_date)
    vampire.csv_utils.add_field(table_name=_zone_table, new_field='end_date', value=end_date)

    # calculate affected crops within admin areas
    # join table to boundary, then extract district etc.
    if admin_boundary is not None:
        #            _boundary_table = os.path.join(os.path.dirname(_output_file), 'crop_admin_table.csv')
        #            impact_analysis.shapefile_to_table(_boundary, _boundary_table)
        #            _merge_output = os.path.join(os.path.dirname(_output_file), 'crop_hazard_merge.csv')
        #            csv_utils.merge_files(file1=_zone_table, file2=_boundary_table, output_file=_merge_output,
        #                                      file1_field='FID_', file2_field='FID_PADDY_')
        _merge_output = _zone_table
        _out_dict = {'area_aff': 'sum'}
        vampire.csv_utils.aggregate_on_field(input=_merge_output, ref_field=admin_field,
                                     output_fields_dict=_out_dict, output=output_file, all_fields=True)

    return None

def reclassify_raster(raster, threshold, output_raster, threshold_direction='LESS_THAN'):
    in_true_constant = 1
    in_false_constant = 0
    rast = arcpy.Raster(raster)
    if threshold_direction == 'LESS_THAN':
        out_ras = arcpy.sa.Con(rast<float(threshold), 1)
    elif threshold_direction == 'EQUALS':
        out_ras = arcpy.sa.Con(rast==float(threshold), 1)
    else:
        out_ras = arcpy.sa.Con(rast>float(threshold), 1)


#     valid = True
#     if threshold_direction == 'LESS_THAN':
#         where_clause = 'VALUE < {0}'.format(threshold)
#         if rast.maximum < threshold:
#             # no values returned
#             valid = False
#     else:
#         where_clause = 'VALUE > {0}'.format(threshold)
#         if rast.minimum > threshold:
#             # all values would be set to null
#             valid = False
#
# #    # Execute Con
# #    out_con = arcpy.sa.Con(in_conditional_raster=raster, in_true_raster_or_constant=in_true_constant,
# #                           in_false_raster_or_constant=in_false_constant, where_clause=where_clause)
# #    out_con.save(output_raster)
#     if valid:
#         out_ras = arcpy.sa.SetNull(in_conditional_raster=raster, in_false_raster_or_constant=1, where_clause=where_clause)
#     else:
#         out_ras = arcpy.sa.Con(rast>float(threshold), 1)
    arcpy.SetRasterProperties_management(out_ras, "GENERIC", nodata=None)
    out_ras.save(output_raster)
    del rast

    return None

def multiply_by_mask(raster, mask, output_raster):
    out_ras = arcpy.sa.Times(raster, mask)
    out_ras.save(output_raster)
    return None

def create_mask(raster, mask, output_raster):
    _mask = arcpy.Raster(mask)
    _raster = arcpy.Raster(raster)
    _new_mask = arcpy.sa.Con(_mask<>0, _mask)
#    _new_mask = arcpy.sa.SetNull(mask, mask, "VALUE = 0")
    out_ras = arcpy.sa.ExtractByMask(_raster, _new_mask)
    out_ras.save(output_raster)
    del _mask
    del _raster
    del _new_mask
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

def calculate_poverty_impact(self, popn_impact_file, popn_impact_field, popn_match_field,
                             poor_file, poor_field, poor_match_field, multiplier,
                             output_file, output_field,
                             start_date, end_date):
    _poverty = geopandas.read_file(poor_file)
    _popn_impact = pandas.read_csv(popn_impact_file)
#    _popn_impact[popn_match_field] = _popn_impact[popn_match_field].map('{:.0f}'.format)
    _merged = pandas.merge(_popn_impact, _poverty[[poor_field, poor_match_field]], how='inner', left_on=popn_match_field, right_on=poor_match_field)
    _merged[output_field] = _merged[popn_impact_field] * (_merged[poor_field]*multiplier)
    _merged['start_date'] = start_date
    _merged['end_date'] = end_date
    _merged.to_csv(output_file)
    return None
