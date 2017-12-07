import logging
import os

import BaseTaskImpl
import directory_utils as directory_utils
import filename_utils as filename_utils

logger = logging.getLogger(__name__)

try:
    import impact_analysis_arc as impact_analysis
    import calculate_statistics_arc as calculate_statistics
except ImportError:
    import impact_analysis_os as impact_analysis
    import calculate_statistics_os as calculate_statistics

class PovertyImpactTaskImpl(BaseTaskImpl.BaseTaskImpl):
    """ Initialise RainfallAnomalyTaskImpl object.

    Abstract implementation class for processing rainfall anomaly.

    """
    def __init__(self, params, vampire_defaults):
        super(PovertyImpactTaskImpl, self).__init__(params, vampire_defaults)
        logger.debug('Initialising Population Impact task')
        return

    def process(self):
        logger.debug("Compute poor population affected by event")
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
        _hazard_field = None
        if 'hazard_field' in self.params:
            _hazard_field = self.params['hazard_field']
        if 'hazard_area_code' in self.params:
            _hazard_match_field = self.params['hazard_area_code']
        else:
            _hazard_match_field = None
        _poverty_pattern = None
        _poverty_dir = None
        _poverty_file = None
        if 'poverty_file' in self.params:
            _poverty_file = self.params['poverty_file']
        elif 'poverty_pattern' in self.params:
            _poverty_dir = self.params['poverty_dir']
            _poverty_pattern = self.params['poverty_pattern']
        else:
            raise BaseTaskImpl.ConfigFileError('No poverty filename "poverty_file" or poverty dir/pattern "poverty_dir / poverty_pattern" set', None)
        if 'poverty_field' in self.params:
            _poverty_field = self.params['poverty_field']
        else:
            _poverty_field = None
        if 'poverty_area_code' in self.params:
            _poverty_match_field = self.params['poverty_area_code']
        else:
            _poverty_match_field = None
        if 'poverty_multiplier' in self.params:
            _poverty_multiplier = self.params['poverty_multiplier']
        else:
            _poverty_multiplier = None

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
        if 'output_field' in self.params:
            _output_field = self.params['output_field']
        else:
            _output_field = None


        self.calculate_impact_poverty(impact_file=_hazard_file, impact_dir=_hazard_dir,
                                    impact_pattern=_hazard_pattern, impact_field=_hazard_field,
                                    impact_match_field=_hazard_match_field,
                                    poor_file=_poverty_file, poor_field=_poverty_field,
                                    poor_match_field=_poverty_match_field, poor_multiplier=_poverty_multiplier,
                                    output_file=_output_file, output_dir=_output_dir,
                                    output_pattern=_output_pattern, output_field=_output_field,
                                    start_date=_start_date, end_date=_end_date)

        return None

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

        _country_name = self.vp.get_country_name(self.vp.get_home_country())
        if impact_match_field is None:
            _impact_match_field = self.vp.get_country(_country_name)['crop_area_code']
        else:
            _impact_match_field = impact_match_field
        if poor_match_field is None:
            _poor_match_field = self.vp.get_country(_country_name)['admin_3_boundary_area_code']
        else:
            _poor_match_field = poor_match_field

        if output_file is None:
            if output_pattern is not None:
                _input_pattern = self.vp.get('hazard_impact', 'vhi_popn_pattern')
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
