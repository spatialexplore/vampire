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

class PopulationImpactTaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(PopulationImpactTaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Population Impact task')
        return

    def process(self):
        logger.debug("Compute population affected by event")

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
        if 'hazard_file' in self.params:
            _hazard_file = self.params['hazard_file']
        elif 'hazard_pattern' in self.params:
            _hazard_dir = self.params['hazard_dir']
            _hazard_pattern = self.params['hazard_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError('No hazard filename "hazard_file" or hazard dir/pattern "hazard_dir / hazard_pattern" set', None)

        _population_pattern = None
        _population_dir = None
        _population_file = None
        if 'population_file' in self.params:
            _population_file = self.params['population_file']
        elif 'population_pattern' in self.params:
            _population_dir = self.params['population_dir']
            _population_pattern = self.params['population_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError('No population filename "population_file" or population dir/pattern "population_dir / population_pattern" set', None)

        if 'boundary_file' in self.params:
            _boundary_file = self.params['boundary_file']
        else:
            raise BaseTaskImpl.ConfigFileError('No boundary file "boundary_file" provided', None)

        if 'boundary_field' in self.params:
            _boundary_field = self.params['boundary_field']
        else:
            _boundary_field = None

        _output_file = None
        _output_dir = None
        _output_pattern = None
        if 'output_file' in self.params:
            _output_file = self.params['output_file']
        elif 'output_pattern' in self.params:
            _output_dir = self.params['output_dir']
            _output_pattern = self.params['output_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError('No output file "output_file" specified', None)

        if 'hazard_threshold' in self.params:
            _threshold = self.params['hazard_threshold']
        else:
            _threshold = None

        self.calculate_impact_popn(hazard_raster=_hazard_file, hazard_dir=_hazard_dir, hazard_pattern=_hazard_pattern,
                                 population_raster=_population_file,
                                 boundary=_boundary_file, b_field=_boundary_field, threshold=_threshold,
                                 output_file=_output_file, output_dir=_output_dir, output_pattern=_output_pattern,
                                 start_date=_start_date, end_date=_end_date, hazard_var=_hazard_var)

    def calculate_impact_popn(self, hazard_raster, hazard_dir, hazard_pattern, threshold,
                              population_raster, boundary, b_field, output_file,
                              output_dir, output_pattern, start_date, end_date, hazard_var='vhi'):
        if threshold is None:
            # get threshold from VampireDefaults
            _threshold = self.vp.get('hazard_impact', '{0}_threshold'.format(hazard_var))
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
                _input_pattern = self.vp.get('hazard_impact', '{0}_input_pattern'.format(hazard_var))
#                _input_pattern = self.vp.get('MODIS_VHI', 'vhi_crop_pattern')
                _output_file = filename_utils.generate_output_filename(os.path.basename(_hazard_raster),
                                                                       _input_pattern, output_pattern)
                _output_file = os.path.join(output_dir, _output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                raise ValueError("No output specified")
        else:
            _output_file = output_file

        if _threshold == '':
            _reclass_raster = _hazard_raster
        else:
            # reclassify hazard raster to generate mask of all <= threshold
            _reclass_raster = os.path.join(os.path.dirname(_output_file), 'hazard_popn_reclass.tif')
            impact_analysis.reclassify_raster(raster=_hazard_raster, threshold=_threshold, output_raster=_reclass_raster)

        if population_raster is None:
            _hazard_raster = _reclass_raster
        else:
            # calculate population from hazard raster and population raster intersection
            _hazard_raster = os.path.join(os.path.dirname(_output_file), 'hazard_popn.tif')
            impact_analysis.create_mask(raster=population_raster, mask=_reclass_raster, output_raster=_hazard_raster)
#            impact_analysis.multiply_by_mask(raster=population_raster, mask=_reclass_raster,
#                                             output_raster=_hazard_raster)
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
        csv_utils.copy_field(table_name=_output_file, new_field='kabupaten_id', copy_field=b_field)

        return None
