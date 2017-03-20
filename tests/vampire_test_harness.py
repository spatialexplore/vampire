import time
import optparse
import os
import traceback
import sys
import vampire

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
            params['country'] = 'Afganistan'
            params['product'] = 'rainfall_longterm_average'
            params['interval'] = 'seasonal'
            params['start_date'] = None
            params['end_date'] = None
            params['download'] = False
            params['data_dir'] = 'U:\\WFP2\\VAMPIRE\\data\\Download\\CHIRPS\\Seasonal\\Statistics_BySeasonal'
            params['lta_dir'] = None #'R:\\WFP2\\VAMPIRE\\data\\Download\\CHIRPS\\Monthly\\AFG'
            params['gdal_dir'] = None
            params['mrt_dir'] = None
            params['crop_only'] = True
            params['overwrite'] = True
            if options.config_file:
                filename = options.config_file
            else:
                filename = 'U:\\WFP2\\WFP_Server\\testing\\testGenCfg.yml'
                options.config_file = filename
            print "Generating config file=", filename
            cf = vampire.ConfigFactory.ConfigFactory('')
            cf.generate_config_file(filename,params)
        if options.config_file:
            config_f = options.config_file
            print 'config file=', config_f
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


