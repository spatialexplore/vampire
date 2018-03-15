import logging
import os

import BaseTaskImpl
import csv_utils as csv_utils
import directory_utils as directory_utils
import filename_utils as filename_utils

logger = logging.getLogger(__name__)

try:
    import impact_analysis_arc as impact_analysis
    import calculate_statistics_arc as calculate_statistics
except ImportError:
    import impact_analysis_os as impact_analysis
    import calculate_statistics_os as calculate_statistics

class AreaImpactTaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise AreaImpactTaskImpl object.

    Abstract implementation class for calculating hazard impact by area.

    """
    def __init__(self, params, vampire_defaults):
        super(AreaImpactTaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Area Impact task')
        return

    def process(self):
        logger.debug("Compute area of event impact")

        if 'hazard_type' in self.params:
            _hazard_var = self.params['hazard_type']
        else:
            raise BaseTaskImpl.ConfigFileError('No hazard type "hazard_type" set', None)

        if 'start_date' in self.params:
            _start_date = self.params['start_date']
        else:
            _start_date = None

        if 'end_date' in self.params:
            _end_date = self.params['end_date']
        else:
            _end_date = None

        _hazard_pattern = None
        _hazard_dir = None
        _hazard_file = None
        _output_file = None
        _output_dir = None
        _output_pattern = None
        if 'hazard_file' in self.params:
            _hazard_file = self.params['hazard_file']
        elif 'hazard_pattern' in self.params:
            _hazard_dir = self.params['hazard_dir']
            _hazard_pattern = self.params['hazard_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError('No hazard filename "hazard_file" or hazard dir/pattern "hazard_dir / hazard_pattern" set', None)

        if 'boundary_file' in self.params:
            _boundary_file = self.params['boundary_file']
        else:
            raise BaseTaskImpl.ConfigFileError('No boundary file "boundary_file" provided', None)

        if 'boundary_field' in self.params:
            _boundary_field = self.params['boundary_field']
        else:
            _boundary_field = None

        if 'output_file' in self.params:
            _output_file = self.params['output_file']
        elif 'output_pattern' in self.params:
            _output_dir = self.params['output_dir']
            _output_pattern = self.params['output_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError('No output file "output_file" or output directory/pattern "output_dir/output_pattern" specified', None)

        if 'hazard_threshold' in self.params:
            _threshold = self.params['hazard_threshold']
        else:
            _threshold = None
        if 'threshold_direction' in self.params:
            _threshold_direction = self.params['threshold_direction']
        else:
            _threshold_direction = None


        self.calculate_impact_area(hazard_raster=_hazard_file, hazard_dir=_hazard_dir, hazard_pattern=_hazard_pattern,
                                   boundary=_boundary_file, b_field=_boundary_field, threshold=_threshold,
                                   threshold_direction=_threshold_direction,
                                   output_file=_output_file, output_dir=_output_dir, output_pattern=_output_pattern,
                                   start_date=_start_date, end_date=_end_date, hazard_var=_hazard_var)

        return

    def calculate_impact_area(self, hazard_raster, hazard_dir, hazard_pattern, threshold, threshold_direction,
                              boundary, b_field, output_file, output_dir, output_pattern, start_date, end_date,
                              hazard_var='vhi'):
        logger.debug("calculate_impact_area with hazard {0}, hazard dir {1}, hazard pattern {2}".format(hazard_raster,
                                                                                                        hazard_dir,
                                                                                                        hazard_pattern))
        if threshold is None:
            # get threshold from VampireDefaults
            _threshold = self.vp.get('hazard_impact', '{0}_threshold'.format(hazard_var))
        else:
            _threshold = threshold
        if threshold_direction is None:
            _threshold_direction = self.vp.get('hazard_impact', '{0}_threshold_direction'.format(hazard_var))
        else:
            _threshold_direction = threshold_direction

        if hazard_raster is None:
            if hazard_pattern is not None:
                _input_files = directory_utils.get_matching_files(hazard_dir, hazard_pattern)
                _hazard_raster = os.path.join(hazard_dir, _input_files[0])
                logger.debug("hazard files: {0}".format(_input_files))
            else:
                raise ValueError("Hazard raster is not specified")
        else:
            _hazard_raster = hazard_raster

        if output_file is None:
            if output_pattern is not None:
#                _input_pattern = self.vp.get('MODIS_VHI', 'vhi_crop_pattern')
                _input_pattern = self.vp.get('hazard_impact', '{0}_input_pattern'.format(hazard_var))
                _output_file = filename_utils.generate_output_filename(os.path.basename(_hazard_raster),
                                                                       _input_pattern, output_pattern)
                _output_file = os.path.join(output_dir, _output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                raise ValueError("No output specified")
        else:
            _output_file = output_file
        logger.debug("Output file: {0}".format(_output_file))

        if _threshold == '':
            _reclass_raster = _hazard_raster
        else:
            if _threshold_direction == '':
                _threshold_direction = 'LESS_THAN'
            # reclassify hazard raster to generate mask of all <= threshold
            _reclass_raster = os.path.join(os.path.dirname(_output_file), 'hazard_area_reclass.tif')
            impact_analysis.reclassify_raster(raster=_hazard_raster, threshold=_threshold,
                                              threshold_direction=_threshold_direction, output_raster=_reclass_raster)

        # calculate impact on boundary
        stats = calculate_statistics.calc_zonal_statistics(raster_file=_reclass_raster, polygon_file=boundary,
                                                           zone_field=b_field, output_table=_output_file)
        # convert to hectares
        # TODO: get multiplier from defaults depending on resolution of hazard raster
        _multiplier = float(self.vp.get('hazard_impact', '{0}_area_multiplier'.format(hazard_var)))
#        csv_utils.calc_field(table_name=_output_file, new_field='area_aff', cal_field='COUNT', multiplier=_multiplier)
        csv_utils.calc_field(table_name=_output_file, new_field='area_aff', cal_field='SUM', multiplier=_multiplier)
        # add start and end date fields and set values
        csv_utils.add_field(table_name=_output_file, new_field='start_date', value=start_date)
        csv_utils.add_field(table_name=_output_file, new_field='end_date', value=end_date)

        csv_utils.copy_field(table_name=_output_file, new_field='kabupaten_id', copy_field=b_field)
        return None
