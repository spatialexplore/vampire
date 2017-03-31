from nose.tools import *
import vampire
import datetime
import errno
import os

def setup():
    print "SETUP!"

def teardown():
    print "TEAR DOWN!"

def write_file(output_file, content):
    try:
        pfile = open(output_file, 'w')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output_file
        # Not a permission error.
        raise
    else:
        with pfile:
            pfile.write(content)

def test_basic():
    print "I RAN!"

def test_chirps_download():
    vp = vampire.VampireDefaults.VampireDefaults()
    filename = "S:\\WFP2\\projects\\vampire_test_output\\test_chirps_download.yml"
    cf = vampire.CHIRPSConfigFactory.CHIRPSConfigFactory('')
    content = cf.generate_download_section('monthly',
                                           vp.get('directories', 'default_download'),
                                           datetime.datetime(2000, 1,1),
                                           datetime.datetime(2014, 1,1))
    write_file(filename, content)

def test_chirps_rainfall_long_term_average():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\chirps_lta'
    vp = vampire.VampireDefaults.VampireDefaults()
    cf = vampire.CHIRPSConfigFactory.CHIRPSConfigFactory('')
    data_dir = vp.get('CHIRPS', 'data_dir')
    lta_dir = vp.get('CHIRPS', 'data_dir')

    # test lta for different intervals, for global, home country and regional country, downloading
    country = ['Global', 'Indonesia', 'Afganistan']
    interval = ['monthly', 'seasonal', 'dekad']
    for c in country:
        for i in interval:
            filename = os.path.join(test_output_dir,
                                    'test_chirps_rainfall_long_term_average_A_{test}_{variant}.yml'.format(
                test=c, variant=i
            ))

            ccode = vp.get_country_code(c)
            if ccode is not None:
                out_dir = os.path.join(lta_dir, '{0}\\{1}\\Statistics_By{0}'.format(
                    i.capitalize(), ccode
                ))
            else:
                out_dir = os.path.join(lta_dir, '{0}\\Statistics_By{0}'.format(
                    i.capitalize()
                ))
            dl_dir = os.path.join(data_dir, '{0}'.format(i.capitalize()))

            content = cf.generate_rainfall_long_term_average_config(c,
                                                            i,
                                                            dl_dir,
                                                            out_dir,
                                                            download=True,
                                                            crop_only=False,
                                                            start_date=None,
                                                            end_date=None
                                                            )
            write_file(filename, content)

    # test lta for different intervals, for global, home country and regional country, no download
    # (existing global CHIRPS files)
    for c in country:
        for i in interval:
            filename = os.path.join(test_output_dir,
                                    'test_chirps_rainfall_long_term_average_B_{test}_{variant}.yml'.format(
                test=c, variant=i
            ))
            dl_dir = os.path.join(data_dir, '{0}'.format(i.capitalize()))
            out_dir = os.path.join(lta_dir, '{0}\\Statistics_By{0}'.format(
                i.capitalize()
            ))
            content = cf.generate_rainfall_long_term_average_config(c,
                                                            i,
                                                            dl_dir,
                                                            out_dir,
                                                            download=False,
                                                            crop_only=False,
                                                            start_date=None,
                                                            end_date=None
                                                            )
            write_file(filename, content)

    # test lta for different intervals, for home country and regional country, using existing global lta and cropping only
    for c in ['Indonesia', 'Afganistan']:
        for i in interval:
            filename = os.path.join(test_output_dir,
                                    'test_chirps_rainfall_long_term_average_C_{test}_{variant}.yml'.format(
                test=c, variant=i
            ))
            dl_dir = os.path.join(data_dir, 'Global\\{1}\\Statistics_By{1}'.format(c.capitalize(), i.capitalize()))
            out_dir = os.path.join(lta_dir, '{0}\\{1}\\Statistics_By{1}'.format(
                c.capitalize(), i.capitalize()
            ))
            content = cf.generate_rainfall_long_term_average_config(c,
                                                            i,
                                                            dl_dir,
                                                            out_dir,
                                                            download=False,
                                                            crop_only=True,
                                                            start_date=None,
                                                            end_date=None
                                                            )
            write_file(filename, content)

    # test monthly lta, global, no download (existing global CHIRPS data files)
    # test monthly lta, global, specific date range, download
    # test monthly lta, global, specific date range, no download (existing global CHIRPS data files)
    # test seasonal lta, global, download
    # test seasonal lta, global, no download (existing global CHIRPS data files)
    # test seasonal lta, global, specific date range, download
    # test seasonal lta, global, specific date range, no download (existing global CHIRPS data files)

    # test dekad lta, global, download
    # test dekad lta, global, no download (existing global CHIRPS data files)
    # test dekad lta, global, specific date range, download
    # test dekad lta, global, specific date range, no download (existing global CHIRPS data files)

    # test monthly lta, regional, download
    # test monthly lta, regional, no download (existing region CHIRPS data files)
    # test monthly lta, regional, existing global CHIRPS data files
    # test monthly lta, regional, existing global lta

    # test seasonal lta, regional, download

def test_generate_chirps_rainfall_anomaly():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\chirps_ra'
    vp = vampire.VampireDefaults.VampireDefaults()
    cf = vampire.CHIRPSConfigFactory.CHIRPSConfigFactory('')
    data_dir = vp.get('CHIRPS', 'data_dir')

    # test lta for different intervals, for global, home country and regional country, downloading
    _country = ['Global', 'Indonesia', 'Afganistan']
    _interval = ['monthly', 'seasonal', 'dekad']
    _lta_dir = vp.get('CHIRPS', 'data_dir')
    for c in _country:
        for i in _interval:
            _filename = os.path.join(test_output_dir,
                                    'test_chirps_rainfall_anomaly_A_{test}_{variant}.yml'.format(
                test=c, variant=i
            ))
            content = cf.generate_header_chirps()
            content += cf.generate_header_directory()
            content += cf.generate_header_run()

            ccode = vp.get_country_code(c)
            out_dir = vp.get('CHIRPS_Rainfall_Anomaly', 'output_dir')
            # if ccode is not None:
            #     out_dir = os.path.join(_lta_dir, '{0}\\{1}\\Statistics_By{0}'.format(
            #         i.capitalize(), ccode
            #     ))
            # else:
            #     out_dir = os.path.join(_lta_dir, '{0}\\Statistics_By{0}'.format(
            #         i.capitalize()
            #     ))
            if ccode is not None:
                dl_dir = os.path.join(data_dir, '{0}\{1}'.format(i.capitalize(), ccode.upper()))
            else:
                dl_dir = os.path.join(data_dir, '{0}'.format(i.capitalize()))
            start_date = datetime.datetime(2016,1,1)
            content += cf.generate_rainfall_anomaly_config(country=c,
                                                          interval=i,
                                                          start_date=start_date,
                                                          cur_dir=dl_dir,
                                                          output_dir=out_dir,
                                                          season='010203'
                                                          )
            write_file(_filename, content)

# test generation of days since last rainfall config
def test_generate_days_since_last_rain():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\chirps_dslr'
    vp = vampire.VampireDefaults.VampireDefaults()
    cf = vampire.CHIRPSConfigFactory.CHIRPSConfigFactory('')
    data_dir = vp.get('CHIRPS', 'data_dir')
    filename = os.path.join(test_output_dir,
                            'test_chirps_days_since_last_rain.yml')

    content = cf.generate_header_chirps()
    content += cf.generate_header_directory()
    content += cf.generate_header_run()
    start_date = datetime.datetime(2016,11,30)
    content += cf.generate_days_since_last_rainfall(country='Indonesia', start_date=start_date, download=True)
    write_file(filename, content)
    return None


# now test processing of config
#def test_process_chirps_rainfall_anomaly():
#    test_input_dir = 'U:\\WFP2\\projects\\vampire_test_output\\chirps_ra'
#    vp = vampire.VampireDefaults.VampireDefaults()
#    cp = vampire.ConfigProcessor.ConfigProcessor()
#    cp.process_config(os.path.join(test_input_dir, 'test_chirps_rainfall_anomaly_A_Global_seasonal.yml'))

def test_generate_vci():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\modis_vci'
    vp = vampire.VampireDefaults.VampireDefaults()
    start_date = datetime.datetime(2016,11,1)
    cf = vampire.MODISConfigFactory.MODISConfigFactory('', country='Indonesia', start_date=start_date, end_date=start_date)
    data_dir = vp.get('MODIS', 'data_dir')
    filename = os.path.join(test_output_dir,
                            'test_modis_vci.yml')
    content = cf.generate_header_directory()
    content += cf.generate_header_run()
    content += cf.generate_vci_config()
    write_file(filename, content)
    return None


def test_generate_tci():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\modis_tci'
    vp = vampire.VampireDefaults.VampireDefaults()
    start_date = datetime.datetime(2016,11,1)
    cf = vampire.MODISConfigFactory.MODISConfigFactory('', country='Indonesia', start_date=start_date, end_date=start_date)
    data_dir = vp.get('MODIS', 'data_dir')
    filename = os.path.join(test_output_dir,
                            'test_modis_tci.yml')
    content = cf.generate_header_directory()
    content += cf.generate_header_run()
    content += cf.generate_tci_config(lst_cur_file=None)
    write_file(filename, content)
    return None

def test_generate_lst_1km():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\modis_lst_1km'
    vp = vampire.VampireDefaults.VampireDefaults()
    start_date = datetime.datetime(2016, 01, 01)
    end_date = datetime.datetime(2017, 02, 01)
    cf = vampire.MODISConfigFactory.MODISConfigFactory('', country='Sri Lanka', start_date=start_date, end_date=end_date)
    data_dir = vp.get('MODIS', 'data_dir')
    lta_dir = vp.get('MODIS', 'data_dir')
    filename = os.path.join(test_output_dir,
                            'test_modis_temperature_1km.yml')
    content = cf.generate_header_directory()
    content += cf.generate_header_run()
    content += cf.generate_tci_config()
    write_file(filename, content)
    return None

def test_generate_modis_lta():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\modis_lta'
    vp = vampire.VampireDefaults.VampireDefaults()
    data_dir = vp.get('MODIS', 'data_dir')
    lta_dir = vp.get('MODIS', 'data_dir')
    start_date = datetime.date(1981, 01, 01)
    # test lta for global, home country and regional country, downloading
    country = ['Global', 'Indonesia', 'Sri Lanka']
    for c in country:
        cf = vampire.MODISConfigFactory.MODISConfigFactory('', country=c, start_date=start_date)
        filename = os.path.join(test_output_dir,
                                'test_modis_temperature_long_term_average_A_{test}.yml'.format(test=c))

        ccode = vp.get_country_code(c)
        content = cf.generate_header_directory()
        content += cf.generate_header_run()
        content += cf.generate_temperature_long_term_average()
        write_file(filename, content)
    return None

def test_generate_vci_plj():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\modis_vci'
    vp = vampire.VampireDefaults.VampireDefaults()
    data_dir = '/srv/Vampire/data/Download'
    filename = os.path.join(test_output_dir,
                            'test_modis_vci_plj.yml')
    start_date = datetime.datetime(2015,11,1)
    cf = vampire.MODISConfigFactory.MODISConfigFactory('', country='Indonesia', start_date=start_date)
    content = cf.generate_header_directory()
    content += cf.generate_header_run()
    content += cf.generate_vci_config(download_dir=data_dir)
    write_file(filename, content)
    return None

def test_generate_vhi():
    test_output_dir = 'S:\\WFP2\\projects\\vampire_test_output\\modis_vhi'
    vp = vampire.VampireDefaults.VampireDefaults()
    start_date = datetime.datetime(2015,11,1)
    cf = vampire.MODISConfigFactory.MODISConfigFactory('', country='Indonesia', start_date=start_date,
                                                       end_date=start_date)
#    cf = vampire.ConfigFactory.ConfigFactory('')
    data_dir = '/srv/Vampire/data/Download'
    filename = os.path.join(test_output_dir,
                            'test_modis_vhi_idn.yml')
    content = cf.generate_header_directory()
    content += cf.generate_header_run()
    content += cf.generate_vci_config()
    content += cf.generate_tci_config()
    content += cf.generate_vhi_config(interval='monthly')
    write_file(filename, content)
    return None
