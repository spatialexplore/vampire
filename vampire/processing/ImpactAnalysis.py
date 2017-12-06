import logging
import os

import vampire.VampireDefaults as VampireDefaults

import vampire.csv_utils as csv_utils
import vampire.directory_utils as directory_utils
import vampire.filename_utils as filename_utils

logger = logging.getLogger(__name__)


try:
    import impact_analysis_arc as impact_analysis
    import calculate_statistics_arc as calculate_statistics
except ImportError:
    import impact_analysis_os as impact_analysis
    import calculate_statistics_os as calculate_statistics


class ImpactAnalysis():
    def __init__(self):
        # load default values from .ini file
        self.vampire = VampireDefaults.VampireDefaults()
        return

    def calculate_impact_poverty(self, impact_file, impact_dir, impact_pattern,
                                 impact_field, impact_match_field,
                                 poor_file, poor_field, poor_multiplier, poor_match_field,
                                 output_file, output_dir, output_pattern, output_field,
                                 start_date, end_date):
        if impact_file is None:
            if impact_pattern is not None:
                _input_files = directory_utils.get_matching_files(impact_dir, impact_pattern)
                _impact_file = os.path.join(impact_dir, _input_files[0])
            else:
                raise ValueError("Hazard raster is not specified")
        else:
            _impact_file = impact_file

        _country_name = self.vampire.get_country_name(self.vampire.get_home_country())
        if impact_match_field is None:
            _impact_match_field = self.vampire.get_country(_country_name)['crop_area_code']
        else:
            _impact_match_field = impact_match_field
        if poor_match_field is None:
            _poor_match_field = self.vampire.get_country(_country_name)['admin_3_boundary_area_code']
        else:
            _poor_match_field = poor_match_field

        if output_file is None:
            if output_pattern is not None:
                _input_pattern = self.vampire.get('hazard_impact', 'vhi_popn_pattern')
                _output_file = filename_utils.generate_output_filename(os.path.basename(_impact_file),
                                                                       _input_pattern, output_pattern)
                _output_file = os.path.join(output_dir, _output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                raise ValueError("No output specified")
        else:
            _output_file = output_file

        if poor_multiplier is None:
            _multiplier = 0.01
        else:
            _multiplier = poor_multiplier

        if output_field is None:
            _output_field = 'poor_aff'
        else:
            _output_field = output_field

        impact_analysis.calculate_poverty_impact(self, popn_impact_file=_impact_file,
                                                 popn_impact_field=impact_field,
                                                 popn_match_field=_impact_match_field,
                                                 poor_file=poor_file, poor_field=poor_field,
                                                 poor_match_field=_poor_match_field,
                                                 multiplier=_multiplier,
                                                 output_file=_output_file, output_field=_output_field,
                                                 start_date=start_date, end_date=end_date)
        return None

    def calculate_impact_popn(self, hazard_raster, hazard_dir, hazard_pattern, threshold,
                              population_raster, boundary, b_field, output_file,
                              output_dir, output_pattern, start_date, end_date, hazard_var='vhi'):
        if threshold is None:
            # get threshold from VampireDefaults
            _threshold = self.vampire.get('hazard_impact', '{0}_threshold'.format(hazard_var))
        else:
            _threshold = threshold

        if hazard_raster is None:
            if hazard_pattern is not None:
                _input_files = directory_utils.get_matching_files(hazard_dir, hazard_pattern)
                _hazard_raster = os.path.join(hazard_dir, _input_files[0])
            else:
                raise ValueError("Hazard raster is not specified")
        else:
            _hazard_raster = hazard_raster

        if output_file is None:
            if output_pattern is not None:
                _input_pattern = self.vampire.get('MODIS_VHI', 'vhi_crop_pattern')
                _output_file = filename_utils.generate_output_filename(os.path.basename(_hazard_raster),
                                                                       _input_pattern, output_pattern)
                _output_file = os.path.join(output_dir, _output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                raise ValueError("No output specified")
        else:
            _output_file = output_file

        # reclassify hazard raster to generate mask of all <= threshold
        _reclass_raster = os.path.join(os.path.dirname(_output_file), 'hazard_popn_reclass.tif')
        impact_analysis.reclassify_raster(raster=_hazard_raster, threshold=_threshold, output_raster=_reclass_raster)

        if population_raster is None:
            _hazard_raster = _reclass_raster
        else:
            # calculate population from hazard raster and population raster intersection
            _hazard_raster = os.path.join(os.path.dirname(_output_file), 'hazard_popn.tif')
            impact_analysis.multiply_by_mask(raster=population_raster, mask=_reclass_raster,
                                             output_raster=_hazard_raster)
        # calculate impact on boundary
        calculate_statistics.calc_zonal_statistics(raster_file=_hazard_raster, polygon_file=boundary,
                                                   zone_field=b_field, output_table=_output_file)

        # add field to table and calculate total for each area
        if population_raster is None:
            csv_utils.calc_field(table_name=_output_file, new_field='popn_aff', cal_field='COUNT', type='LONG')
        else:
            csv_utils.calc_field(table_name=_output_file, new_field='popn_aff', cal_field='SUM', type='LONG')

        # add start and end date fields and set values
        csv_utils.add_field(table_name=_output_file, new_field='start_date', value=start_date)
        csv_utils.add_field(table_name=_output_file, new_field='end_date', value=end_date)

        return None

    def calculate_impact_area(self, hazard_raster, hazard_dir, hazard_pattern, threshold,
                              boundary, b_field, output_file, output_dir, output_pattern, start_date, end_date,
                              hazard_var='vhi'):
        if threshold is None:
            # get threshold from VampireDefaults
            _threshold = self.vampire.get('hazard_impact', '{0}_threshold'.format(hazard_var))
        else:
            _threshold = threshold

        if hazard_raster is None:
            if hazard_pattern is not None:
                _input_files = directory_utils.get_matching_files(hazard_dir, hazard_pattern)
                _hazard_raster = os.path.join(hazard_dir, _input_files[0])
            else:
                raise ValueError("Hazard raster is not specified")
        else:
            _hazard_raster = hazard_raster

        if output_file is None:
            if output_pattern is not None:
                _input_pattern = self.vampire.get('MODIS_VHI', 'vhi_crop_pattern')
                _output_file = filename_utils.generate_output_filename(os.path.basename(_hazard_raster),
                                                                       _input_pattern, output_pattern)
                _output_file = os.path.join(output_dir, _output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                raise ValueError("No output specified")
        else:
            _output_file = output_file

        # reclassify hazard raster to generate mask of all <= threshold
        _reclass_raster = os.path.join(os.path.dirname(_output_file), 'hazard_area_reclass.tif')
        impact_analysis.reclassify_raster(raster=_hazard_raster, threshold=_threshold, output_raster=_reclass_raster)

        # calculate impact on boundary
        stats = calculate_statistics.calc_zonal_statistics(raster_file=_reclass_raster, polygon_file=boundary,
                                                           zone_field=b_field, output_table=_output_file)
        # convert to hectares
        # TODO: get multiplier from defaults depending on resolution of hazard raster
        csv_utils.calc_field(table_name=_output_file, new_field='area_aff', cal_field='COUNT', multiplier=6.25)
        # add start and end date fields and set values
        csv_utils.add_field(table_name=_output_file, new_field='start_date', value=start_date)
        csv_utils.add_field(table_name=_output_file, new_field='end_date', value=end_date)

        return None

    def calculate_impact_crops(self, hazard_raster, hazard_dir, hazard_pattern, threshold,
                               crop_boundary, crop_dir, crop_pattern, crop_field,
                               admin_boundary, admin_boundary_field,
                               output_file, output_dir, output_pattern, start_date, end_date,
                               hazard_var='vhi', intersect=False):

        if threshold is None:
            # get threshold from VampireDefaults
            _threshold = self.vampire.get('hazard_impact', '{0}_threshold'.format(hazard_var))
        else:
            _threshold = threshold

        if hazard_raster is None:
            if hazard_pattern is not None:
                _input_files = directory_utils.get_matching_files(hazard_dir, hazard_pattern)
                _hazard_raster = os.path.join(hazard_dir, _input_files[0])
            else:
                raise ValueError("Hazard raster is not specified")
        else:
            _hazard_raster = hazard_raster

        if crop_boundary is None:
            if crop_pattern is not None:
                _crop_files = directory_utils.get_matching_files(crop_dir, crop_pattern)
                _crop_boundary = os.path.join(crop_dir, _crop_files[0])
            else:
                raise ValueError("Crop boundary file not specified.")
        else:
            _crop_boundary = crop_boundary

        if output_file is None:
            if output_pattern is not None:
                _input_pattern = self.vampire.get('MODIS_VHI', 'vhi_pattern')
                _output_file = filename_utils.generate_output_filename(os.path.basename(_hazard_raster),
                                                                       _input_pattern, output_pattern)
                _output_file = os.path.join(output_dir, _output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                raise ValueError("No output specified")
        else:
            _output_file = output_file

        if output_dir is None:
            _output_dir = os.path.dirname(output_file)
        else:
            _output_dir = output_dir

        impact_analysis.calculate_crop_impact(_hazard_raster, _threshold, hazard_var,
                                              crop_boundary, crop_field,
                                              admin_boundary, admin_boundary_field,
                                              _output_file,
                                              start_date, end_date, intersect=False)

#         # reclassify hazard raster to generate mask of all <= threshold
#         _reclass_raster = os.path.join(os.path.dirname(_output_file), 'hazard_crops_reclass.tif')
#         impact_analysis.reclassify_raster(raster=_hazard_raster, threshold=_threshold, output_raster=_reclass_raster)
#
#         _zone_table = os.path.join(_output_dir, 'hazard_crops_table.csv')
#
#         # calculate impact on boundary
#         # if have admin boundary as well, intersect the two boundaries first, then dissolve after the join to
#         # calculate crop impact per admin area
#         if admin_boundary is None:
#             _boundary = _crop_boundary
#             _zone_field = crop_field
#         else:
#             if intersect:
#                 _boundary_output = os.path.join(os.path.dirname(_output_file), 'crop_admin_intersection.shp')
#                 impact_analysis.intersect_boundaries([_crop_boundary, admin_boundary], _boundary_output)
#                 _boundary = _boundary_output
#                 _zone_field = 'fid'
#             else:
#                 _boundary = _crop_boundary
#                 _zone_field = 'fid'
#         stats = calculate_statistics.calc_zonal_statistics(raster_file=_reclass_raster, polygon_file=_boundary,
#                                                            zone_field=_zone_field, output_table=_zone_table)
#
#         # convert to hectares
#         # TODO: get multiplier from defaults depending on resolution of hazard raster
#         csv_utils.calc_field(table_name=_zone_table, new_field='area_aff', cal_field='COUNT', multiplier=6.25)
#         # add start and end date fields and set values
#         csv_utils.add_field(table_name=_zone_table, new_field='start_date', value=start_date)
#         csv_utils.add_field(table_name=_zone_table, new_field='end_date', value=end_date)
#
#         # calculate affected crops within admin areas
#         # join table to boundary, then extract district etc.
#         if admin_boundary is not None:
# #            _boundary_table = os.path.join(os.path.dirname(_output_file), 'crop_admin_table.csv')
# #            impact_analysis.shapefile_to_table(_boundary, _boundary_table)
# #            _merge_output = os.path.join(os.path.dirname(_output_file), 'crop_hazard_merge.csv')
# #            csv_utils.merge_files(file1=_zone_table, file2=_boundary_table, output_file=_merge_output,
# #                                      file1_field='FID_', file2_field='FID_PADDY_')
#             _merge_output = _zone_table
#             _out_dict = {'area_aff':'sum'}
#             csv_utils.aggregate_on_field(input=_merge_output, ref_field=admin_boundary_field,
#                                          output_fields_dict=_out_dict, output=_output_file, all_fields=True)
#
        return None
