import GeoserverManager
import VampireDefaults

try:
    import ArcGISServerManager
except ImportError:
    print "ArcPy not supported"

#try:
#    import gis_server_arc as gisserver
#except ImportError:
#    import gis_server_geoserver as gisserver

class GISServerInterface:
    'Base Class for managing uploading of products to GIS server'

    def __init__(self, gis_server_type):
        self.server_type = gis_server_type
        # load default values from .ini file
        self.vampire = VampireDefaults.VampireDefaults()
        if self.vampire.get('vampire', 'gis_server').lower == 'arcgis':
            try:
                self.gis_server = ArcGISServerManager.ArcGISServerManager()
            except ImportError:
                print 'Missing libraries for ArcPy. These are required for GIS Server type "arcgis"'
                self.gis_server = None
        elif self.vampire.get('vampire', 'gis_server').lower == 'geoserver':
            self.gis_server = GeoserverManager.GeoserverManager()
        else:
            self.gis_server = None
        return

    def upload_to_GIS_server(self, product, input_file, input_dir,
                             input_pattern, start_date, end_date):
        if self.gis_server:
            self.gis_server.upload_to_GIS_server(product, input_file, input_dir, input_pattern,
                                                 start_date, end_date, self.vampire)


