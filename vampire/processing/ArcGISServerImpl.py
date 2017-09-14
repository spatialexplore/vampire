import arcpy
import os
import xml.dom.minidom as DOM
import logging
logger = logging.getLogger(__name__)

class ArcGISServerImpl(object):

    def __init__(self, vp):
        self.vp = vp
        # # LOG_FILENAME = 'Vampire_log.log'
        # # logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
        # date1 = time.strftime('%c')
        # geodatabase = vp.get('geodatabase', 'config')
        # config = ast.literal_eval(geodatabase)
        # product = config['product']
        # keycode = config['keycode']
        # country = config['country']
        # host = config['postgreHost']
        # dba = config['dba']
        # dbapass = config['dbapass']
        # sdeuser = config['sdeuser']
        # sdepass = config['sdepass']
        # proj = config['proj']
        # file_path = config['gdbpath']
        # directory = file_path+'\\'+country
        # storingConfig = config['storingConfig']
        # datafolder = config['sourcedata'] + '\\' + country
        #
        # server_url = config['server_url']
        # use_arcgis_desktop_staging_folder = config['use_arcgis_desktop_staging_folder']
        # username = config['username']
        # password = config['password']
        # ws = config['ws']
        # sdeCatalog = config['sdeCatalog']
        # template = config['template']
        # summary = config['summary']
        # tags = config['tags']
        # description = config['description']
        return

    def publish(self, product):
        try:

            if self.vp.get('geodatabase', 'storingConfig') == 'file':
                logger.debug("using file geodatabase")
                # create gdb directory if it doesn't exist
                self.check_data_dir(self.vp.get('geodatabase', 'gdbpath'))
                # create file geodatabase if it doesn't exist
                _gdb_name = self.check_file_GDB(product.product_name, self.vp.get('geodatabase', 'gdbpath'))
                _mosaic_db = os.path.join(_gdb_name, '{0}'.format(product.product_name))
                _ags_name = product.product_name
                _layer = _mosaic_db
            elif self.vp.get('geodatabase', 'storingConfig') == 'ent':
                logger.debug("Using enterprise geodatabase")
                _enterprise_gdb_name = '{0}_{1}'.format(self.vp.get('vampire', 'home_country').lower(), product.product_name)
                self.create_enterprise_GDB(_enterprise_gdb_name, self.vp.get('geodatabase','host'),
                                           self.vp.get('geodatabase', 'dba'), self.vp.get('geodatabase', 'dbapass'),
                                           self.vp.get('geodatabase', 'sdeuser'),
                                           self.vp.get('geodatabase', 'sdepass'),
                                           self.vp.get('geodatabase', 'keycode'))
#                gdb = "Database Connections/"+egdbname+".sde"
                _gdb_name = "Database Connections/{0}.sde".format(_enterprise_gdb_name)
                _mosaic_db = os.path.join(_gdb_name, '{0}.sde.{1}'.format(_enterprise_gdb_name, _enterprise_gdb_name))
                _ags_name = _enterprise_gdb_name
                _layer = os.path.join(os.path.join(self.vp.get('geodatabase', 'sdeCatalog'),
                                                     '{0}.sde'.format(_enterprise_gdb_name)), _enterprise_gdb_name)
            #     countProduct = country.lower() + "_" + x
            #     self.createagsfile(ws, countProduct, server_url, username, password)
            #     sdeCon = sdeCatalog+countProduct+'.sde/'
            #     fc = sdeCon+countProduct
            else:
                logger.error('Unrecognised geodatabase storing config')
                return
#                MDS = gdb + '/' + egdbname + ".sde." + egdbname
#                    gdbname = directory+'\\'+x+'.gdb'
#                    MDS = gdbname + '\\' + x
                # check if mosaic database exists, and create if necessary
            if arcpy.Exists(_mosaic_db):
                logger.debug("Mosaic dataset {0} already exists".format(_mosaic_db))
            else:
                self.create_mosaic_dataset(_gdb_name, product.product_name)
                logger.debug("Mosaic Dataset {0} created".format(_mosaic_db))
            # add product raster to mosaic dataset
            self.add_raster_to_MDS(_mosaic_db, product.product_dir)
            # add start and end date fields to mosaic dataset if necessary
            self.add_date_field(_mosaic_db)
            #  compute statistics
            self.update_mosaic_statistics(_mosaic_db)
            # set start and end date for product in mosaic dataset
            self.update_date_fields(_mosaic_db, product)
            _ws = self.vp.get('geodatabase', 'ws')
            self.create_ags_file(_ws, _ags_name,
                                 self.vp.get('geodatabase', 'server_url'),
                                 self.vp.get('geodatabase', 'username'), self.vp.get('geodatabase', 'password'))
#                    fc1 = os.path.join(directory, x+'.gdb')
#                    fc = os.path.join(fc1, x)
            if arcpy.Exists(_layer):
                logger.debug("data {0} is available".format(product.product_name))
            else:
                logger.debug("data {0} is not available".format(product.product_name))
            _connection_file = os.path.join(_ws, '{0}.ags'.format(product.product_name))
            arcpy.AddDataStoreItem(_connection_file, "FOLDER", product.product_name,
                                   self.vp.get('geodatabase', 'gdbpath'), self.vp.get('geodatabase', 'gdbpath'))
            arcpy.ValidateDataStoreItem(_connection_file, "FOLDER", product.product_name)
            _service_desc_draft = os.path.join(_ws, '{0}.sddraft'.format(product.product_name))
            _service_desc = os.path.join(_ws, '{0}.sd'.format(product.product_name))
            self.create_image_SD_draft(product, _layer, _service_desc_draft,
                                       product.product_name, _connection_file)
            self.insert_RTF_file(product.product_name, _service_desc_draft)
            if not os.path.exists(_service_desc):
                self.analyze_SD_draft(_service_desc_draft, _service_desc)
            else:
                logger.debug("file {0} already exists".format(_service_desc))
            if not os.path.exists(_connection_file):
                logger.debug("file {0} does not exist".format(_connection_file))
            else:
                logger.debug("file {0} already exists".format(_connection_file))
                arcpy.UploadServiceDefinition_server(_service_desc, _connection_file)
            logger.debug(_connection_file)

            # elif self.vp.get('geodatabase', 'storingConfig') == 'ent':
            #     logger.debug("Using enterprise geodatabase")
            #     self.createEntGDB(host, x, dba, dbapass, sdeuser, sdepass, keycode)
            #     egdbname = country.lower() + '_' + x
            #     gdb = "Database Connections/"+egdbname+".sde"
            #     MDS = gdb + '/' + egdbname + ".sde." + egdbname
            #     if arcpy.Exists(MDS):
            #         print("Mosaic dataset "+MDS+" already exist")
            #     else:
            #         self.createMosaicDataset(gdb,egdbname)
            #         logging.debug(date1 +": Mosaic Dataset "+egdbname+" is created")
            #
            #     #print(MDS)
            #     workspace = datafolder + "/" + x
            #     self.addRastertoMDS(MDS, workspace)
            #     self.update_mosaic_statistics(MDS)
            #     self.addDateField(MDS)
            #     self.updateDateField(MDS, x)
            #
            #     countProduct = country.lower() + "_" + x
            #     self.createagsfile(ws, countProduct, server_url, username, password)
            #     sdeCon = sdeCatalog+countProduct+'.sde/'
            #     fc = sdeCon+countProduct
            #     print(fc)
            #     if arcpy.Exists(fc):
            #         print("data "+x+" is available")
            #     else:
            #         print("data "+x+" is not availabe")
            #     con = os.path.join(ws, x + ".ags")
            #     service = x
            #     sddraft = os.path.join(ws, x + ".sddraft")
            #     sd = os.path.join(ws, x + ".sd")
            #     self.createImageSDDraft(fc, sddraft, service, con)
            #     self.insertRTFFile(x, sddraft)
            #     if not os.path.exists(sd):
            #         self.analyzeSDDraft(sddraft, sd)
            #     else:
            #         print("file "+sd+" already exist")
            #     if not os.path.exists(con):
            #         print("file "+con+" is not exist")
            #     else:
            #         print("file "+con+" already exist")
            #         arcpy.UploadServiceDefinition_server(sd, con)
            #     print(con)
        except Exception, e:
            logger.debug(e.message)
        return None

    def create_file_GDB(self, gdb_name, location):
        arcpy.CreateFileGDB_management(location, gdb_name, "CURRENT")


    def create_enterprise_GDB(self, gdb_name, host, dba, dbapass, sdeuser, sdepass, keycode):
#        gdb_name = country.lower()+'_'+product
        #print(gdb_name)
        arcpy.CreateEnterpriseGeodatabase_management("PostgreSQL", host, gdb_name, "DATABASE_AUTH", dba, dbapass,
                                                     "SDE_SCHEMA", sdeuser, sdepass, "", keycode)
        logging.debug("Enterprise Geodatabase {0} is created".format(gdb_name))
        arcpy.CreateDatabaseConnection_management("Database Connections",
                                                  "{0}.sde".format(gdb_name),
                                                  "POSTGRESQL",
                                                  host,
                                                  "DATABASE_AUTH",
                                                  sdeuser,
                                                  sdepass,
                                                  "SAVE_USERNAME",
                                                  gdb_name,
                                                  "#",
                                                  "POINT_IN_TIME",
                                                  "#",
                                                  "5/19/2017 8:43:41 AM")
        logger.debug("Database connection for geodatabase {0} is created".format(gdb_name))
        return None

    def check_data_dir(self, file_path):
        if not os.path.exists(file_path):
            os.makedirs(file_path)
            logger.debug("Geodatabase directory created")
        else:
            logger.debug("Geodatabase directory already exists")
        return None

    def check_file_GDB(self, gdb_name, directory):
        _file_GDB_path = os.path.join(directory, '{0}.gdb'.format(gdb_name))
        if not os.path.exists(_file_GDB_path):
            self.create_file_GDB(gdb_name, directory)
            logger.debug("File Geodatabase " + gdb_name + " created")
        else:
            logger.debug("File Geodatabase  " + gdb_name + " already exists")
        return _file_GDB_path

    def create_mosaic_dataset(self, gdb, dataset):
        _proj = self.vp.get('geodatabase', 'proj')
        arcpy.CreateMosaicDataset_management(gdb, dataset, _proj, "", "", "NONE", "")
        return None

    def add_raster_to_MDS(self, mds, folder):
        arcpy.AddRastersToMosaicDataset_management(mds, "Raster Dataset", folder,
                                                   "UPDATE_CELL_SIZES", "UPDATE_BOUNDARY", "NO_OVERVIEWS", "", "0", "1500",
                                                   "", "", "SUBFOLDERS", "OVERWRITE_DUPLICATES", "NO_PYRAMIDS", "NO_STATISTICS",
                                                   "NO_THUMBNAILS", "", "NO_FORCE_SPATIAL_REFERENCE")
        return None

    def update_mosaic_statistics(self, mosaic_dataset):
        logger.debug('updating mosaic statistics')
        arcpy.SetMosaicDatasetProperties_management(mosaic_dataset, use_time="ENABLED", start_time_field="start_date",
                                                    end_time_field="end_date",)
        arcpy.management.CalculateStatistics(mosaic_dataset)
        arcpy.management.BuildPyramidsandStatistics(mosaic_dataset, 'INCLUDE_SUBDIRECTORIES', 'BUILD_PYRAMIDS',
                                                    'CALCULATE_STATISTICS')
        arcpy.RefreshCatalog(mosaic_dataset)
        return None

    # def eomday(self, year, month):
    #     days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #     d = days_per_month[month - 1]
    #     if month == 2 and (year % 4 == 0 and year % 100 != 0 or year % 400 == 0):
    #         d = 29
    #     return d
    #
    # def get_year_month(self, name, product):
    #     if product == 'rainfall_anomaly_1_month':
    #         print("analomay")
    #         productPattern = self.vp.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_monthly_pattern')
    #         print("product pattern : "+productPattern)
    #         regex = re.compile(productPattern)
    #         result = regex.match(name)
    #         f_year = result.group('year')
    #         f_month = result.group('month')
    #         lastday = eomday(int(f_year), int(f_month))
    #         dateStart = date(int(f_year),int(f_month),1)
    #         dateEnd = date(int(f_year),int(f_month),int(lastday))
    #         return(dateStart, dateEnd)
    #     elif product == 'spi_1_month':
    #         print("spi 1 month")
    #         productPattern = vp.get('CHIRPS_SPI', 'spi_regional_monthly_pattern')
    #         print("product pattern : "+productPattern)
    #         regex = re.compile(productPattern)
    #         result = regex.match(name)
    #         f_year = result.group('year')
    #         f_month = result.group('month')
    #         lastday = eomday(int(f_year), int(f_month))
    #         dateStart = date(int(f_year),int(f_month),1)
    #         dateEnd = date(int(f_year),int(f_month),int(lastday))
    #         return(dateStart, dateEnd)
    #     elif product == 'rainfall_anomaly_3_month':
    #         print("3 monthly rainfall anomaly")
    #         productPattern = vp.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_seasonal_pattern')
    #         print("product pattern : "+productPattern)
    #         regex = re.compile(productPattern)
    #         result = regex.match(name)
    #         print(result)
    #         f_year = result.group('year')
    #         print(f_year)
    #         f_season = result.group('season')
    #         print(f_season, f_season[0:2])
    #         if int(f_season[4:6]) < int(f_season[0:2]):
    #             print(int(f_season[4:6]), " lebih kecil dari ", int(f_season[0:2]))
    #             f_year_end = int(f_year)+1
    #         else:
    #             print(int(f_season[4:6]), " lebih besar dari ", int(f_season[0:2]))
    #             f_year_end = int(f_year)
    #         lastday = eomday(int(f_year_end), int(f_season[4:6]))
    #         dateStart = date(int(f_year),int(f_season[0:2]),1)
    #         dateEnd = date(int(f_year_end),int(f_season[4:6]),int(lastday))
    #         print("resturn ", dateStart, dateEnd)
    #         return(dateStart, dateEnd)
    #     elif product == 'spi_3_month':
    #         print("3 monthly spi")
    #         productPattern = vp.get('CHIRPS_SPI', 'spi_regional_seasonal_pattern')
    #         print("product pattern : "+productPattern)
    #         regex = re.compile(productPattern)
    #         result = regex.match(name)
    #         print(result)
    #         f_year = result.group('year')
    #         print(f_year)
    #         f_season = result.group('season')
    #         print(f_season, f_season[0:2])
    #         if int(f_season[4:6]) < int(f_season[0:2]):
    #             print(int(f_season[4:6]), " lebih kecil dari ", int(f_season[0:2]))
    #             f_year_end = int(f_year)+1
    #         else:
    #             print(int(f_season[4:6]), " lebih besar dari ", int(f_season[0:2]))
    #             f_year_end = int(f_year)
    #         lastday = eomday(int(f_year_end), int(f_season[4:6]))
    #         dateStart = date(int(f_year),int(f_season[0:2]),1)
    #         dateEnd = date(int(f_year_end),int(f_season[4:6]),int(lastday))
    #         print("resturn ", dateStart, dateEnd)
    #         return(dateStart, dateEnd)
    #     elif product == 'rainfall_anomaly_dekad':
    #         print("Dekad rainfall anomaly")
    #         productPattern = vp.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_dekad_pattern')
    #         regex = re.compile(productPattern)
    #         result = regex.match(name)
    #         f_year = result.group('year')
    #         f_month = result.group('month')
    #         f_dekad = result.group('dekad')
    #         if f_dekad == '1':
    #             dateStart = date(int(f_year),int(f_month),1)
    #             dateEnd = date(int(f_year),int(f_month),10)
    #         elif f_dekad == '2':
    #             dateStart = date(int(f_year),int(f_month),11)
    #             dateEnd = date(int(f_year),int(f_month),20)
    #         elif f_dekad == '3':
    #             lastday = eomday(int(f_year), int(f_month))
    #             dateStart = date(int(f_year),int(f_month),21)
    #             dateEnd = date(int(f_year),int(f_month),lastday)
    #         return(dateStart, dateEnd)
    #     elif product == 'spi_dekad':
    #         print("Dekad SPI")
    #         productPattern = vp.get('CHIRPS_SPI', 'spi_regional_dekad_pattern')
    #         regex = re.compile(productPattern)
    #         result = regex.match(name)
    #         f_year = result.group('year')
    #         f_month = result.group('month')
    #         f_dekad = result.group('dekad')
    #         if f_dekad == '1':
    #             dateStart = date(int(f_year),int(f_month),1)
    #             dateEnd = date(int(f_year),int(f_month),10)
    #         elif f_dekad == '2':
    #             dateStart = date(int(f_year),int(f_month),11)
    #             dateEnd = date(int(f_year),int(f_month),20)
    #         elif f_dekad == '3':
    #             lastday = eomday(int(f_year), int(f_month))
    #             dateStart = date(int(f_year),int(f_month),21)
    #             dateEnd = date(int(f_year),int(f_month),lastday)
    #         return(dateStart, dateEnd)
    #     else:
    #         return(None, None)


    def add_date_field(self, mosaic_dataset):
        _field_name = ["start_date", "end_date"]
        _field_type = "DATE"
        for i in _field_name:
            if arcpy.ListFields(mosaic_dataset, i):
                logger.debug("Field already exists")
            else:
                arcpy.AddField_management(mosaic_dataset, i, _field_type)
        return None

    def update_date_fields(self, mosaic_dataset, product):
        fields = ['Name', 'start_date', 'end_date']
        logger.debug("product : "+product.product_name)
        with arcpy.da.UpdateCursor(mosaic_dataset, fields) as cursor:
            logger.debug(cursor)
            for row in cursor:
                if row[1] == None or row[2] == None:
                    _filename = str(row[0])+".tif"
                    logger.debug("filename: "+_filename)
#                    start_date, end_date = self.get_year_month(_filename, productX)
                    logger.debug("tes ", product.valid_from_date, product.valid_to_date)
                    if product.valid_from_date == None:
                        logger.debug("cant find match naming template")
                    else:
                        logger.debug(product.valid_from_date, product.valid_to_date)
                        logger.debug("tes")
                        row[1] = product.valid_from_date
                        row[2] = product.valid_to_date
                elif row[1] is not None:
                    logger.debug("row1 is none")
                    logger.debug(row[0])
                cursor.updateRow(row)
        return None

    def create_ags_file(self, ws, product_name, server_url, username, password):
        arcpy.mapping.CreateGISServerConnectionFile("PUBLISH_GIS_SERVICES",
                                                ws, product_name,
                                                server_url,
                                                "ARCGIS_SERVER",
                                                False,
                                                ws,
                                                username,
                                                password,
                                                "SAVE_USERNAME")
        logger.debug("Connection Server file is created")
        return None

    def create_image_SD_draft(self, product, layer, sd_draft, service, connection_file):
        _product_summary = product.summary
        _product_tags = product.tags
#        summaryP = summary[product]
#        tagsP = tags[product]
        arcpy.CreateImageSDDraft(raster_or_mosaic_layer=layer, out_sddraft=sd_draft, service_name=service,
                                 server_type='FROM_CONNECTION_FILE', connection_file_path=connection_file,
                                 copy_data_to_server=False,
                                 folder_name='Climate', summary=_product_summary, tags=_product_tags)
        logger.debug("SDDraft file for {0} is created".format(product.product_name))
        return None


    def analyze_SD_draft(self, sd_draft, sd):
        _analysis = arcpy.mapping.AnalyzeForSD(sd_draft)
        logger.debug("Service Definition analysis")
        for key in ('messages', 'warnings', 'errors'):
            logger.debug('---- {0} ---'.format(key.upper()))
            _vars = _analysis[key]
            for ((message, code), layer_list) in _vars.iteritems():
                logger.debug("    {0} (CODE {1})".format(message, code))
                logger.debug("       applies to:")
                for layer in layer_list:
                    logger.debug(layer.name)
        if _analysis['errors'] == {}:
            # Execute StageService
            arcpy.StageService_server(sd_draft, sd)
            # Execute UploadServiceDefinition
        else:
            # if the sddraft analysis contained errors, display them
            logger.debug(_analysis['errors'])
        return None

    def insert_RTF_file(self, product, sd_draft):
        _file_RTF = product.template_file #template[product]
        logger.debug('_file_RTF : {0} in {1}'.format(_file_RTF, sd_draft))
        doc = DOM.parse(sd_draft)
        x = doc.getElementsByTagName("PropertySetProperty")
        for i in x:
            y = i.getElementsByTagName("Key")
            for j in y:
                if j.childNodes[0].nodeValue == "rasterFunctions":
                    price = i.getElementsByTagName("Value")
                    for p in price:
                        if p.firstChild == None:
                            p.appendChild(doc.createTextNode(_file_RTF))
                            print("RTF data {0} is added".format(_file_RTF))
                        else:
                            p.firstChild.replaceWholeText(_file_RTF)
                            print("RTF data {0} is added".format(_file_RTF))
        services___ = doc.getElementsByTagName('TypeName')
        for service__ in services___:
            if service__.firstChild.data == 'WMSServer':
                service__.parentNode.getElementsByTagName('Enabled')[0].firstChild.data = 'true'
        with open(sd_draft, "wb") as f:
            doc.writexml(f)
        return None

