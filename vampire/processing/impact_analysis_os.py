import csv
import logging
import os

import fiona
import geopandas
import numpy as np
import ogr
import pandas
import rasterio
import rasterio.mask

import calculate_statistics_os as calculate_statistics
import raster_utils
import csv_utils as csv_utils

logger = logging.getLogger(__name__)

def calculate_poverty_impact(self, popn_impact_file, popn_impact_field, popn_match_field,
                             poor_file, poor_field, poor_match_field, multiplier,
                             output_file, output_field,
                             start_date, end_date):
    _poverty = geopandas.read_file(poor_file)
    _popn_impact = pandas.read_csv(popn_impact_file)
    _popn_impact[popn_match_field] = _popn_impact[popn_match_field].map('{:.0f}'.format)
    _merged = pandas.merge(_popn_impact, _poverty[[poor_field, poor_match_field]], how='inner', left_on=popn_match_field, right_on=poor_match_field)
    _merged[output_field] = _merged[popn_impact_field] * (_merged[poor_field]*multiplier)
    _merged['start_date'] = start_date
    _merged['end_date'] = end_date
    _merged.to_csv(output_file)
    return None

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
    _boundary = crop_boundary
    _zone_field = admin_field.lower() #'fid'
###    don't do intersect
#    if admin_boundary is None:
#        _boundary = crop_boundary
#        _zone_field = crop_field
#    else:
#        if intersect:
#            _boundary_output = os.path.join(_output_dir, 'crop_admin_intersection.shp')
#            intersect_boundaries([crop_boundary, admin_boundary], _boundary_output)
#            _boundary = _boundary_output
#            _zone_field = 'fid'
#        else:
#            _boundary = crop_boundary
#            _zone_field = 'fid'
###
    stats = calculate_statistics.calc_zonal_statistics(raster_file=_reclass_raster, polygon_file=_boundary,
                                                       zone_field=_zone_field, output_table=_zone_table)

    # convert to hectares
    # TODO: get multiplier from defaults depending on resolution of hazard raster
    csv_utils.calc_field(table_name=_zone_table, new_field='area_aff', cal_field='COUNT', multiplier=6.25)
    # add start and end date fields and set values
    csv_utils.add_field(table_name=_zone_table, new_field='start_date', value=start_date)
    csv_utils.add_field(table_name=_zone_table, new_field='end_date', value=end_date)

    # calculate affected crops within admin areas
    # join table to boundary, then extract district etc.
    if admin_boundary is not None:
        #            _boundary_table = os.path.join(os.path.dirname(_output_file), 'crop_admin_table.csv')
        #            impact_analysis.shapefile_to_table(_boundary, _boundary_table)
        #            _merge_output = os.path.join(os.path.dirname(_output_file), 'crop_hazard_merge.csv')
        #            csv_utils.merge_files(file1=_zone_table, file2=_boundary_table, output_file=_merge_output,
        #                                      file1_field='FID_', file2_field='FID_PADDY_')
        _merge_output = _zone_table
        _out_dict = {'area_aff': 'sum', 'crops_ha': 'sum'}
        csv_utils.aggregate_on_field(input=_merge_output, ref_field=admin_field,
                                     output_fields_dict=_out_dict, output=output_file, all_fields=True)
        # calculate percentage
        csv_utils.calc_field(table_name=output_file, new_field='total_area_ha', cal_field='crops_ha') #,
#                             multiplier=100.0)
        csv_utils.calc_pc_field(table_name=output_file, new_field='impact_pc', numerator_field='area_aff',
                                denominator_field='total_area_ha')
        _gf = geopandas.GeoDataFrame.from_file(admin_boundary)
#        _gf = geopandas.GeoDataFrame.from_file('C:\PRIMA\data\Shapefiles\Boundaries\National\lka_bnd_adm3_dsd_nbro_wgs84.shp')

        csv_utils.calc_normalized_field(table_name=output_file, new_field='impact_norm',
                                        area_field='area_aff', total_field='total_area_ha', admin_area=_gf)

        return None

def reclassify_raster(raster, threshold, output_raster,
                      threshold_direction='LESS_THAN'):
    _threshold = float(threshold)
    with rasterio.open(raster) as ras_r:
        _profile = ras_r.profile.copy()
        _ras_a = ras_r.read(1, masked=True)
        if threshold_direction == 'LESS_THAN':
            _dst_r = np.ma.masked_where(_ras_a >= _threshold, _ras_a)
            _dst_r.data[_ras_a < _threshold] = 1
        elif threshold_direction == 'EQUALS':
            _dst_r = np.ma.masked_where(_ras_a <> _threshold, _ras_a)
            _dst_r.data[_ras_a == _threshold] = 1
        else:
            _dst_r = np.ma.masked_where(_ras_a <= _threshold, _ras_a)
            _dst_r.data[_ras_a > _threshold] = 1

#        _dst_r = np.ma.masked_where(_ras_a > _threshold, _ras_a)
#        _dst_r.data[_ras_a <= _threshold] = 1
        _dst_r = _dst_r.filled(-9999)
        _profile.update(dtype=rasterio.int16, nodata=-9999)
        with rasterio.open(output_raster, 'w', **_profile) as dst:
            dst.write(_dst_r.astype(rasterio.int16), 1)

    # _driver = gdal.GetDriverByName('GTiff')
    # _file = gdal.Open(raster)
    # _band = _file.GetRasterBand(1)
    # _ras_a = _band.ReadAsArray()
    #
    # _ras_a[np.where(_ras_a <= int(threshold))] = 1
    # _ras_a[np.where(_ras_a > int(threshold))] = -3000
    #
    # _out = _driver.Create(output_raster, _file.RasterXSize, _file.RasterYSize, 1)
    # _out.GetRasterBand(1).WriteArray(_ras_a)
    # _proj = _file.GetProjection()
    # _georef = _file.GetGeoTransform()
    # _out.SetProjection(_proj)
    # _out.SetGeoTransform(_georef)
    # _out.FlushCache()

    return None

def multiply_by_mask(raster, mask, output_raster):
    _tmp_ras = os.path.join(os.path.dirname(raster), 'tmp_{0}'.format(os.path.basename(raster)))
    raster_utils.reproject_image_to_master(master=mask, slave=raster, output=_tmp_ras)

    with rasterio.open(_tmp_ras) as ras:
        _ras_a = ras.read(1, masked=True)
        _profile = ras.profile.copy()
        with rasterio.open(mask) as _mask_r:
            # TODO check if same size/projection
            _mask_a = _mask_r.read(1, masked=True)
            _dst_r = np.multiply(_ras_a,_mask_a)
            _dst_r = _dst_r.filled(-9999)
            _profile.update(dtype=rasterio.float32, nodata=-9999)
            with rasterio.open(output_raster, 'w', **_profile) as dst:
                dst.write(_dst_r.astype(rasterio.float32), 1)
                print "saved multiply result in: ", output_raster
    return None


def create_mask(raster, mask, output_raster):
    _tmp_mask = os.path.join(os.path.dirname(mask), 'tmp_{0}'.format(os.path.basename(mask)))
    raster_utils.reproject_image_to_master(master=raster, slave=mask, output=_tmp_mask)
#    _tmp_ras = os.path.join(os.path.dirname(raster), 'tmp_{0}'.format(os.path.basename(raster)))
#    raster_utils.reproject_image_to_master(master=mask, slave=raster, output=_tmp_ras)
#    with rasterio.open(_tmp_ras) as ras:
    with rasterio.open(raster) as ras:
        _ras_a = ras.read(1, masked=True)
        _profile = ras.profile.copy()
        with rasterio.open(_tmp_mask) as _mask_r:
#        with rasterio.open(mask) as _mask_r:
            # TODO check if same size/projection
            _mask_a = _mask_r.read(1, masked=True)
            _dst_r = np.ma.masked_where(_mask_a==0, _mask_a)
            _dst_r.data[:] = _ras_a
            _profile.update(dtype=rasterio.float32, nodata=-9999)
            _dst_r = _dst_r.filled(-9999)
            with rasterio.open(output_raster, 'w', **_profile) as dst:
                dst.write(_dst_r.astype(rasterio.float32), 1)
                print "saved multiply result in: ", output_raster

    return None

def shapefile_to_table(input_file, output_file):
    if os.path.splitext(output_file)[1] != '.dbf':
        _output = '{0}{1}'.format(os.path.splitext(os.path.basename(output_file))[0], '.dbf')
        _output_csv = '{0}{1}'.format(os.path.splitext(output_file)[0], '.csv')
    else:
        _output = os.path.basename(output_file)
        _output_csv = '{0}{1}'.format(os.path.splitext(output_file)[0], '.csv')
    _csv_file = open(_output_csv, 'wb')
    _ds = ogr.Open(input_file)
    _layer = _ds.GetLayer()
    _dfn = _layer.GetLayerDefn()
    _nfields = _dfn.GetFieldCount()
    fields = []
    for i in range(_nfields):
        fields.append(_dfn.GetFieldDefn(i).GetName())
    _csv_writer = csv.DictWriter(_csv_file, fields)
    _csv_writer.writeheader()
    for feat in _layer:
        _attributes = feat.items()
        _csv_writer.writerow(_attributes)

    # clean up
    del _csv_writer, _layer, _ds
    _csv_file.close()
    #    arcpy.TableToTable_conversion(input, os.path.dirname(output), os.path.splitext(_output)[0])
#    vampire_tmp.csv_utils.convert_dbf_to_csv(os.path.join(os.path.dirname(output), _output), _output_csv)
    return None

def intersect_boundaries(boundary_list, boundary_output):
    _g_list = []
    for b in boundary_list:
        _df = geopandas.GeoDataFrame.from_file(b)
        _g_list.append(_df)

#    g1 = geopandas.GeoDataFrame.from_file("crime_stat.shp")
#    g2 = geopandas.GeoDataFrame.from_file("population.shp")
    _new_data = []
    _new_columns = []
    _res_intersection = geopandas.overlay(_g_list[0], _g_list[1], how='intersection')

    for index, _data in _g_list[0].iterrows():
        for index2, _data2 in _g_list[1].iterrows():
            if _data['geometry'].intersects(_data2['geometry']):
                _new_dict = {}
                for x in list(_data.columns.values):
                    _new_dict[x] = _data[x]
                    _new_columns.append(x)
                for y in list(_data2.columns.values):
                    if _new_dict.has_key(y):
                        _new_key = '{0}_data2'.format(y)
                        _new_dict[_new_key] = _data2[y]
                        _new_columns.append(_new_key)
                    else:
                        _new_dict[y] = _data2[y]
                _new_dict['geometry'] = _data['geometry'].intersection(_data2['geometry'])
                _new_columns.append('geometry')
#               _new_dict['area'] = _data['geometry'].intersection(_data2['geometry']).area
                _new_data.append(_new_dict)

    df = geopandas.GeoDataFrame(_new_data,columns=_new_columns)
    df.to_file(boundary_output)
    df.head()
#    arcpy.Intersect_analysis(in_features=boundary_list, out_feature_class=boundary_output)
    return None

def mask_with_shapefile(raster_file, mask_file, output_file):
    with fiona.open(mask_file, "r") as shapefile:
        geoms = [feature["geometry"] for feature in shapefile]

    with rasterio.open(raster_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, geoms)
        out_meta = src.meta.copy()

    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(out_image)

    return None