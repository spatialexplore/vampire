import arcpy


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

def calc_field(table_name, new_field, cal_field, multiplier=1.0, type='DOUBLE'):
    arcpy.AddField_management(table_name, new_field, type)
    fields = (new_field, cal_field)
    with arcpy.da.UpdateCursor(in_table=table_name, field_names=fields) as cursor:
        for row in cursor:
            val = row[1]
            row[0] = int(val*multiplier)
            cursor.updateRow(row)
    return None