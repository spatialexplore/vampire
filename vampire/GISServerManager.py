import VampireDefaults

try:
    import gis_server_arc as gisserver
except ImportError:
    import gis_server_geoserver as gisserver

class GISServerManager:
    'Base Class for managing uploading of products to GIS server'

    def __init__(self, gis_server_type):
        self.server_type = gis_server_type
        # load default values from .ini file
        self.vampire = VampireDefaults.VampireDefaults()
        return

    def upload_to_GIS_server(self, product, start_date):
        gisserver.upload_to_GIS_server(product, start_date, self.vampire)


