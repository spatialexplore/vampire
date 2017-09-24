import time
import optparse
import os
import traceback
import sys
import datetime
import vampire.VampireDefaults
import vampire.ConfigFactory
import vampire.ConfigProcessor

if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        parser.add_option ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option ('-c', '--config', dest='config_file', action='store', help='config filename')
        parser.add_option ('-g', '--generate', dest='generate_config', action='store', help='generate config')
        (options, args) = parser.parse_args()
        if options.verbose: print time.asctime()
        config_f = ""
        if options.generate_config:
            params = {}
            params['country'] = 'Indonesia'
            params['product'] = 'days_since_last_rain'
            params['interval'] = 'daily'
            params['output'] = 'S:\WFP2\PRISM\configs\test_dslr.yml'
            params['start_date'] = _start_date = datetime.datetime.strptime('2014/07/01', "%Y/%m/%d")
            params['end_date'] = None
            params['download'] = True
            params['data_dir'] = 'S:\\WFP2\\PRISM\\data\\Download\\IMERG\\Daily'
            params['gdal_dir'] = None
            params['mrt_dir'] = None
            params['crop_only'] = False
            params['overwrite'] = True
            # params['country'] = 'Afganistan'
            # params['product'] = 'rainfall_longterm_average'
            # params['interval'] = 'seasonal'
            # params['start_date'] = None
            # params['end_date'] = None
            # params['download'] = False
            # params['data_dir'] = 'U:\\WFP2\\VAMPIRE\\data\\Download\\CHIRPS\\Seasonal\\Statistics_BySeasonal'
            # params['lta_dir'] = None #'R:\\WFP2\\VAMPIRE\\data\\Download\\CHIRPS\\Monthly\\AFG'
            # params['gdal_dir'] = None
            # params['mrt_dir'] = None
            # params['crop_only'] = True
            # params['overwrite'] = True
            if options.config_file:
                filename = options.config_file
            else:
                filename = 'S:\\WFP2\\PRISM\\configs\\test_dslr.yml'
                options.config_file = filename
            print "Generating config file=", filename
            vampire.config_generator.generate_config_file(filename, params)
#            cf = vampire.ConfigFactory.ConfigFactory('')
#            cf.generate_config_file(filename, params)
        if options.config_file:
            config_f = options.config_file
            print 'config file=', config_f
            vp = vampire.VampireDefaults.VampireDefaults()
            cp = vampire.ConfigProcessor.ConfigProcessor()
            cp.process_config(config_f)
        if options.verbose: print time.asctime()
        if options.verbose: print 'TOTAL TIME IN MINUTES:',
        if options.verbose: print (time.time() - start_time) / 60.0
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)


