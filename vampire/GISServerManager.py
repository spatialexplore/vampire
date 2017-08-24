import VampireDefaults
import GeoserverManager

try:
    import gis_server_arc as gisserver
except ImportError:
    import gis_server_geoserver as gisserver

class GISServerManager:
    'Base Class for managing uploading of products to GIS server'

    def __init__(self):
        # load default values from .ini file
        self.vampire = VampireDefaults.VampireDefaults()
        return

    def upload_to_GIS_server(self, product, input_file, input_dir, input_pattern,
                             start_date, end_date, vp):
        gisserver.upload_to_GIS_server(product, input_file, input_dir, input_pattern,
                                        start_date, end_date, vp)


