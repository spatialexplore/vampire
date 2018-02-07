import cookielib
import datetime
import json
import os
import urllib2

import dateutil
import dateutil.relativedelta
import gdal
import osr

import BaseTaskImpl
import directory_utils
import filename_utils
import VampireDefaults

#import h5py
import logging
logger = logging.getLogger(__name__)
try:
    import calculate_statistics_arc as calculate_statistics
    import precipitation_analysis_arc as precip_analysis
except ImportError:
    import calculate_statistics_os as calculate_statistics
    import precipitation_analysis_os as precip_analysis


class IMERGTasksImpl():
    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, process_type, params, vampire_defaults=None):
        if process_type not in cls.subclasses:
            raise ValueError('Bad process type {}'.format(process_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[process_type](params, vp)

@IMERGTasksImpl.register_subclass('download')
class IMERGDownloadTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise IMERGDownloadTask object.

    Implementation class for downloading IMERG products.

    """
    def __init__(self, params, vampire_defaults):
        super(IMERGDownloadTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising IMERG download task')
        return

    def process(self):
        logger.debug("Downloading IMERG data")
        try:
            output_dir = self.params['output_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No ouput directory 'output_dir' specified.", e)
        _dates = None
        _start_date = None
        _end_date = None
        _overwrite = False
        if 'dates' in self.params:
            _dates = self.params['dates']
        if 'start_date' in self.params:
            _start_date = self.params['start_date']
        if 'end_date' in self.params:
            _end_date = self.params['end_date']
        if 'overwrite' in self.params:
            _overwrite = True
        self.download_data(output_dir, self.params['interval'], dates=_dates, start_date=_start_date,
                         end_date=_end_date, overwrite=_overwrite)
        return None

    def download_data(self, output_dir, interval, dates=None, start_date=None, end_date=None, overwrite=False):
        """ Download IMERG precipitation data for given interval.

        Download IMERG precipitation data for given interval. Will download all available data unless start
        and/or end dates are provided.

        Parameters
        ----------
        output_dir : str
            Filename of raster file
        interval : str
            Filename of vector file
        dates : str
            Name of field labelling the zones within vector file
        start_date : str
            Filename of output table (.dbf or .csv)
        end_date : str
            F
        overwrite : boolean

        Returns
        -------
        None
            Returns None

        """
        username = self.vp.get('MODIS', 'user')
        password = self.vp.get('MODIS', 'password')

        # Create a password manager to deal with the 401 reponse that is returned from
        # Earthdata Login
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, "https://urs.earthdata.nasa.gov", username, password)

        # Create a cookie jar for storing cookies. This is used to store and return
        # the session cookie given to use by the data server (otherwise it will just
        # keep sending us back to Earthdata Login to authenticate).  Ideally, we
        # should use a file based cookie jar to preserve cookies between runs. This
        # will make it much more efficient.
        cookie_jar = cookielib.CookieJar()

        # Install all the handlers.

        opener = urllib2.build_opener(
            urllib2.HTTPBasicAuthHandler(password_manager),
            #urllib2.HTTPHandler(debuglevel=1),    # Uncomment these two lines to see
            #urllib2.HTTPSHandler(debuglevel=1),   # details of the requests/responses
            urllib2.HTTPCookieProcessor(cookie_jar))
        urllib2.install_opener(opener)

        _start_date = None
        _end_date = None
        if dates is None:
            # download between start and end dates
            if start_date is not None and end_date is not None:
                _start_date = start_date
                _end_date = end_date
            else:
                # do something else!
                if start_date is not None:
                    _start_date = start_date
                    _end_date = start_date
                else: # end_date is not None
                    _end_date = end_date
                    _start_date = end_date
        else:
            # get from first day of month for first date in list to last day in month of last date in list
            _start_date = datetime.datetime.strptime(dates[0], '%Y-%m')
            _end_date = datetime.datetime.strptime(dates[-1], '%Y-%m') + dateutil.relativedelta.relativedelta(day=31)
        _i_date = _start_date
        files_list = []
        while _i_date < _end_date:
            _imerg_file = '3B-DAY-L.MS.MRG.3IMERG.{0}{1:0>2}{2:0>2}-S000000-E235959.V04.nc4'.format(_i_date.year,
                                                                                                    _i_date.month,
                                                                                                    _i_date.day)
            if not os.path.exists(os.path.join(output_dir, _imerg_file)):
                # The url of the file we wish to retrieve
                # url = url_base product/year/month/imerg_file
                _url = '{0}{1}/{2}/{3:0>2}/{4}'.format(self.vp.get('IMERG', 'base_url'),
                                                   self.vp.get('IMERG', 'default_product'),
                                                   _i_date.year, _i_date.month, _imerg_file)

                # Create and submit the request. There are a wide range of exceptions that
                # can be thrown here, including HTTPError and URLError. These should be
                # caught and handled.
                _request = urllib2.Request(_url)
                _response = urllib2.urlopen(_request)
                _outfile = os.path.join(output_dir, _imerg_file)
                total_size = int(_response.info().getheader('Content-Length').strip())
                downloaded = 0
                CHUNK = 256 * 10240
                with open(_outfile, 'wb') as fp:
                    while True:
                        chunk = _response.read(CHUNK)
                        downloaded += len(chunk)
                        if not chunk: break
                        fp.write(chunk)
                files_list.append(_outfile)
            # get the .xml too
            _imerg_xml = '3B-DAY-L.MS.MRG.3IMERG.{0}{1:0>2}{2:0>2}-S000000-E235959.V04.nc4.xml'.format(_i_date.year,
                                                                                                _i_date.month,
                                                                                                _i_date.day)
            _imerg_xml_output = '3B-DAY-L.MS.MRG.3IMERG.{0}{1:0>2}{2:0>2}-S000000-E235959.V04.nc4.aux.xml'.format(_i_date.year,
                                                                                                _i_date.month,
                                                                                                _i_date.day)
            _url = '{0}{1}/{2}/{3:0>2}/{4}'.format(self.vp.get('IMERG', 'base_url'),
                                                   self.vp.get('IMERG', 'default_product'),
                                                   _i_date.year, _i_date.month, _imerg_xml)
            if not os.path.exists(os.path.join(output_dir, _imerg_xml)):
                _request = urllib2.Request(_url)
                _response = urllib2.urlopen(_request)
                _body = _response.read()
                _outfile = os.path.join(output_dir, _imerg_xml_output)
                _outfp = open(_outfile, 'wb')
                _outfp.write(_body)
            _i_date += datetime.timedelta(days=1)
        return files_list

@IMERGTasksImpl.register_subclass('extract')
class IMERGExtractTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise IMERGExtractTask object.

    Implementation class for extracting precipitation from IMERG products.

    """
    def __init__(self, params, vampire_defaults):
        super(IMERGExtractTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising IMERG extract task')
        self.params = params
        self.vp = vampire_defaults
        return

    def process(self):
        logger.debug("Extracting IMERG data")
        try:
            _input_dir = self.params['input_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No input directory 'input_dir' set.", e)
        try:
            _output_dir = self.params['output_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No output directory 'output_dir' set.", e)
        if 'file_pattern' in self.params:
            _file_pattern = self.params['file_pattern']
        else:
            _file_pattern = self.vp.get('IMERG', 'global_daily_pattern')
        if 'output_pattern' in self.params:
            _output_pattern = self.params['output_pattern']
        else:
            _output_pattern = self.vp.get('IMERG', 'global_precip_output_pattern')
        patterns = (_file_pattern, _output_pattern)
        if 'layer' in self.params:
            _subset_name = self.params['layer']
        else:
            _subset_name = self.vp.get('IMERG', 'subset_name')

        if 'overwrite' in self.params:
            _overwrite = self.params['overwrite']
        else:
            _overwrite = False
        _files = None

        _spectral_subset = json.loads(self.vp.get('IMERG', 'spectral_subset'))

        new_files = self._extract_subset(_input_dir, _output_dir, patterns,
                                         _spectral_subset, _subset_name, _overwrite)
        return new_files

    def _extract_subset(self, input_dir, output_dir, patterns, subset, subset_name, overwrite = False):
        logger.info('entering _extract_subset')
        _all_files = directory_utils.get_matching_files(input_dir, patterns[0])
        if not _all_files:
            logger.debug('Extracting subset {0}. No files found in {1} with pattern {2}'.format(
                subset_name, input_dir, patterns[0]))
            logger.info('No files found in ' + input_dir + ', please check directory and try again')
            return -1

        # check output directory exists and create it if not
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        new_files = []
        _sr = osr.SpatialReference()
        _sr.ImportFromEPSG(4326)
        for _ifl in _all_files:
            # generate output file
            _nfl = filename_utils.generate_output_filename(os.path.basename(_ifl), patterns[0], patterns[1])
            _ofl = os.path.join(output_dir, _nfl)
            if not os.path.exists(_ofl) or overwrite == True:
                try:
                    gdal.SetConfigOption( 'CPL_DEBUG', 'ON' )
                    gdal.UseExceptions()
                    _name_str = 'HDF5:"{0}"://{1}'.format(_ifl, subset_name)
                    src_ds = gdal.Open(_name_str)
                    _proj = src_ds.GetProjection()
                    print _proj
                    _geotransform = src_ds.GetGeoTransform()
                    print _geotransform
                    src_ds.SetProjection(_sr.ExportToWkt())
                    src_ds.SetGeoTransform([-180, 0.1, 0, -90, 0, 0.1])
                    print src_ds.RasterCount
                    print src_ds.GetMetadata()
                    t = src_ds.RasterXSize
                    _band = src_ds.GetRasterBand(1)
                    _data = _band.ReadAsArray().T
                    stats = _band.GetStatistics( True, True )
                    if stats is None:
                        continue

                    logger.debug('[ STATS ] =  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f' %
                                 (stats[0], stats[1], stats[2], stats[3]))
                    ysize,xsize = _data.shape
                    tif = gdal.GetDriverByName('GTiff').Create(_ofl, xsize, ysize, eType=gdal.GDT_Float32)
                    tif.SetProjection(src_ds.GetProjection())
                    tif.SetGeoTransform(list(src_ds.GetGeoTransform()))
                    band = tif.GetRasterBand(1)
                    band.WriteArray(_data)
                    band.FlushCache()
                    band.SetNoDataValue(-9999.900390625)
                    tif = None # closes file
                except RuntimeError, e:
                    logger.debug('Unable to open file')
                    return -1
                if src_ds is None:
                    logger.debug('Unable to open file {0}'.format(_ifl))
                    raise RuntimeError
                new_files.append(_ofl)
        logger.info('leaving _extract_subset')
        return new_files

