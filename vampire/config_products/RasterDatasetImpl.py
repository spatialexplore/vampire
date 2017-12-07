import logging
logger = logging.getLogger(__name__)

class RasterDatasetImpl(object):
    """ Initialise RasterDatasetImpl object.

    Abstract implementation class for Raster datasets.

    """
    def __init__(self):
        logger.debug('Initialising Raster dataset')
        return

    """ Generate crop process section for raster datasets.

    Generate VAMPIRE config file process for raster dataset cropping.

    Parameters
    ----------
    input_dir : string
        Path for raster file.
    output_dir : string
        Path for output of cropped file.
    file_pattern : string
        Pattern to match to find input file.
    output_pattern : string
        Pattern to use with input file pattern to generate output filename.
    boundary_file : string
        Path to boundary file to be used to clip the raster.
    no_data : boolean
        Flag indicating whether areas clipped out of the raster should be set to No Data.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def generate_crop_section(self, input_dir, output_dir, file_pattern, output_pattern, boundary_file,
                              no_data=False):
        file_string = """
    # Crop data
    - process: Raster
      type: crop
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'
      boundary_file: {boundary_file}""".format(
                           input_dir=input_dir,
                           output_dir=output_dir,
                           file_pattern=file_pattern,
                           output_pattern=output_pattern,
                           boundary_file=boundary_file
                           )
        if no_data:
            file_string += """
      no_data:
      """
        else:
            file_string +="""
      """
        return file_string

    def generate_mask_section(self, input_file, input_dir, input_pattern, output_file, output_dir, output_pattern,
                              boundary_file, no_data=False):
        cfg_string = """
    # Mask data with boundary
    - process: Raster
      type: apply_mask"""
        if input_file is not None:
            cfg_string += """
      raster_file: {input_file}""".format(input_file)
        else:
            cfg_string += """
      raster_dir: {input_dir}
      raster_pattern: '{file_pattern}'""".format(input_dir=input_dir, file_pattern=input_pattern)
        cfg_string += """
      polygon_file: {boundary_file}""".format(boundary_file=boundary_file)
        if output_file is not None:
            cfg_string += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            cfg_string += """
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'""".format(output_dir=output_dir,
                                                   output_pattern=output_pattern,)
        if no_data:
            cfg_string += """
      no_data:
          """
        else:
            cfg_string += """
          """
        return cfg_string

    """ Generate crop process section for raster datasets.

    Generate VAMPIRE config file process for raster dataset cropping.

    Parameters
    ----------
    input_dir : string
        Path for raster file.
    output_dir : string
        Path for output of cropped file.
    file_pattern : string
        Pattern to match to find input file.
    output_pattern : string
        Pattern to use with input file pattern to generate output filename.
    boundary_file : string
        Path to boundary file to be used to clip the raster.
    no_data : boolean
        Flag indicating whether areas clipped out of the raster should be set to No Data.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def generate_mosaic_section(self, input_dir, output_dir, file_pattern, output_pattern, mosaic_method='MAXIMUM',
                              no_data=False):
        file_string = """
    # mosaic data
    - process: Raster
      type: mosaic
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'
      mosaic_method: {mosaic_method}""".format(
                           input_dir=input_dir,
                           output_dir=output_dir,
                           file_pattern=file_pattern,
                           output_pattern=output_pattern,
                           mosaic_method=mosaic_method
                           )
        if no_data:
            file_string += """
      no_data:
      """
        else:
            file_string +="""
      """
        return file_string
