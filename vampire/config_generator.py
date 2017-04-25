import errno
import time
import optparse
import sys
import datetime
import os
import traceback
import MODISConfigFactory
import CHIRPSConfigFactory

def generate_config_file(output_file, params):
    if os.path.exists(output_file):
        try:
            pfile = open(output_file, 'a')
        except IOError as e:
            if e.errno == errno.EACCES:
                return "Error creating file " + output_file
            # Not a permission error.
            raise
        except Exception, e:
            raise
    else:
        try:
            pfile = open(output_file, 'w')
        except IOError as e:
            raise

    with pfile:
        cf = CHIRPSConfigFactory.CHIRPSConfigFactory(name='cf')
        mf = MODISConfigFactory.MODISConfigFactory(name='mf', country=params['country'],
                                                   start_date=params['start_date'], end_date=params['start_date'])
        pfile.write(cf.generate_header_directory())
        if 'product' in params:
            if params['product'].lower() == "rainfall_anomaly":
                pfile.write(cf.generate_header_chirps())
                pfile.write(cf.generate_header_run())
                pfile.write(cf.generate_rainfall_anomaly_config(params['country'], params['interval'],
                                                                params['start_date']))
            elif params['product'].lower() == "vhi":
                pfile.write(mf.generate_header_run())
                pfile.write(mf.generate_vci_config())
                pfile.write(mf.generate_tci_config())
                pfile.write(mf.generate_vhi_config())
            elif params['product'].lower() == "rainfall_longterm_average":
                pfile.write(cf.generate_header_chirps())
                pfile.write(cf.generate_header_run())
                pfile.write(cf.generate_rainfall_long_term_average_config(params['country'],
                                                                            params['interval']
                                                                            ))
        pfile.close()
    return 0

if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        parser.add_option('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option('-c', '--country', dest='country', action='store', help='country name')
        parser.add_option('-p', '--product', dest='product', action='store', help='product')
        parser.add_option('-o', '--output', dest='output', action='store', help='output filename')
        parser.add_option('-i', '--interval', dest='interval', action='store', help='interval')
        parser.add_option('-d', '--start_date', dest='start_date', action='store', help='start year-month')
        (options, args) = parser.parse_args()
        #if len(args) < 1:
        #    parser.error ('missing argument')
        params = {}
        if options.verbose: print time.asctime()
        _country = None
        if options.country:
            _country = options.country
            print 'country=', _country
            params['country'] = _country
        _product = None
        if options.product:
            _product = options.product
            print 'product=', _product
            params['product'] = _product
        _output = None
        if options.output:
            _output = options.output
            print 'output=', _output
        _interval = None
        if options.interval:
            _interval = options.interval
            print 'interval=', _interval
            params['interval'] = _interval
        _start_date = None
        if options.start_date:
            try:
                _start_date = datetime.datetime.strptime(options.start_date, "%Y-%m")
            except ValueError:
                # can't parse string, try with day as well
                _start_date = datetime.datetime.strptime(options.start_date, "%Y-%m-%d")
            print 'start_date=', _start_date
            params['start_date'] = _start_date
        generate_config_file(_output, params)
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
