import GISServerManager


class ArcGISServerManager(GISServerManager.GISServerManager):

    def __init__(self):
        GISServerManager.GISServerManager.__init__(self)
        return

    def upload_to_GIS_server(self, product, input_file, input_dir, input_pattern,
                             start_date, end_date, vp):
        print "Not yet implemented."
