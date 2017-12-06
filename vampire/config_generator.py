import datetime
import errno
import optparse
import os
import sys
import time
import traceback

import config_products.BaseImpactProduct as BaseImpactProduct
import config_products.BaseProduct as BaseProduct


def generate_config_file(output_file, params):
    if os.path.exists(output_file):
        try:
            pfile = open(output_file, 'w')
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
        # cf = CHIRPSConfigFactory.CHIRPSConfigFactory(name='cf')
        # _end_date = params['start_date']
        # _valid_to = None
        # if 'end_date' in params:
        #     _end_date = params['end_date']
        # mf = MODISConfigFactory.MODISConfigFactory(name='mf', country=params['country'],
        #                                            start_date=params['start_date'], end_date=_end_date)
        # if 'valid_from' in params:
        #     _valid_from = params['valid_from']
        # else:
        #     _valid_from = params['start_date']
        # imf = ImpactConfigFactory.ImpactConfigFactory(name='imf', country=params['country'],
        #                                               start_date=_valid_from, end_date=params['start_date'])
        # pfile.write(cf.generate_header_directory())
        if 'product' in params:
            _product = BaseProduct.BaseProduct.create(product_type=params['product'], country=params['country'],
                                                      product_date=params['start_date'], interval=params['interval']) #params=params)
            pfile.write(_product.generate_header())
            pfile.write("""
run:
""")
            pfile.write(_product.generate_config())

            if 'mask' in params and params['mask'] == True:
                pfile.write(_product.generate_mask_config())

            if 'impact' in params and params['impact'] == True:
                if params['product'] == 'vhi':
                    _area_impact = BaseImpactProduct.BaseImpactProduct.create(impact_type='vhi_impact_area',
                                                                              country=params['country'],
                                                                              valid_from_date=_product.valid_from_date,
                                                                              valid_to_date=_product.valid_to_date
                                                                              )
                    pfile.write(_area_impact.generate_config(hazard_file=_product.product_file,
                                                             hazard_dir=_product.product_dir,
                                                             hazard_pattern=_product.product_pattern))
                    _popn_impact = BaseImpactProduct.BaseImpactProduct.create(impact_type='vhi_impact_popn',
                                                                              country=params['country'],
                                                                              valid_from_date=_product.valid_from_date,
                                                                              valid_to_date=_product.valid_to_date
                                                                              )
                    pfile.write(_popn_impact.generate_config(hazard_file=_product.product_file,
                                                             hazard_dir=_product.product_dir,
                                                             hazard_pattern=_product.product_pattern))
                    if 'publish' in params and params['publish'] == True:
                        pfile.write(_popn_impact.generate_publish_config())
                        pfile.write(_area_impact.generate_publish_config())

                elif params['product'] == 'flood_forecast':
                    _area_impact = BaseImpactProduct.BaseImpactProduct.create(impact_type='flood_impact_area',
                                                                              country=params['country'],
                                                                              valid_from_date=_product.valid_from_date,
                                                                              valid_to_date=_product.valid_to_date
                                                                              )
                    pfile.write(_area_impact.generate_config(hazard_file=_product.product_file,
                                                             hazard_dir=_product.product_dir,
                                                             hazard_pattern=_product.product_pattern))


            if 'publish' in params and params['publish'] == True:
                pfile.write(_product.generate_publish_config())

#            if params['product'] == 'vhi':
#                if 'mask' in params:
#                    if params['mask'] == True:
#                        _mask = True
#                        _masked_vhi = BaseProduct.BaseProduct.create(product_type=params['masked_vhi'], country=params['country'],
#                                                                     product_date=params['start_date'], interval=params['interval'])
#                        pfile.write(_masked_vhi.generate_config())
#                    else:
#                        _mask = False
#                else:
#                    _mask = False
#                if params['impact'] == True:
#                    _popn_impact = BaseProduct.BaseProduct.create(product_type='vhi_impact_popn', country=params['country'],
#                                                                  product_date=params['start_date'], interval=params['interval'])
#                    pfile.write(_popn_impact.generate_config(masked=_mask))

#            if params['product'].lower() == "rainfall_anomaly":
#                pfile.write(cf.generate_header_chirps())
#                pfile.write(cf.generate_header_run())
#                pfile.write(cf.generate_rainfall_anomaly_config(params['country'], params['interval'],
#                                                                params['start_date']))
#             if params['product'].lower() == "evi_longterm_average":
#                 pfile.write(mf.generate_header_run())
#                 if 'interval' in params:
#                     _interval = params['interval']
#                 else:
#                     _interval = '16Days'
#                 pfile.write(mf.generate_evi_long_term_average(interval=_interval))
            # elif params['product'].lower() == "vhi":
            #     pfile.write(mf.generate_header_run())
            #     pfile.write(mf.generate_vci_config())
            #     if 'interval' in params:
            #         _interval = params['interval']
            #     else:
            #         _interval = '16Days'
            #     pfile.write(mf.generate_tci_config(interval=_interval))
            #     pfile.write(mf.generate_vhi_config())
            #     _mask = False
            #     if 'mask' in params:
            #         if params['mask'] == True:
            #             _mask = True
            #             pfile.write(mf.generate_mask())
            #     if params['impact'] == True:
            #         pfile.write(imf.generate_impact(product=params['product'], interval=_interval, masked=_mask))
            #     if params['publish'] == True:
            #         pf = PublishConfigFactory.PublishConfigFactory(name='pf', country=params['country'],
            #                                           start_date=_valid_from, end_date=params['start_date'])
            #         pfile.write(pf.generate_publish_gis(product=params['product'], interval=_interval, masked=_mask))
            # elif params['product'].lower() == "rainfall_longterm_average":
            #     pfile.write(cf.generate_header_chirps())
            #     pfile.write(cf.generate_header_run())
            #     pfile.write(cf.generate_rainfall_long_term_average_config(params['country'],
            #                                                                 params['interval']
            #                                                                 ))
            # elif params['product'].lower() == "spi":
            #     pfile.write(cf.generate_header_chirps())
            #     pfile.write(cf.generate_header_run())
            #     pfile.write(cf.generate_standardized_precipitation_index_config(params['country'], params['interval'],
            #                                                     params['start_date']))
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
        parser.add_option('-d', '--start_date', dest='start_date', action='store', help='start year-month-day')
        parser.add_option('-e', '--end_date', dest='end_date', action='store', help='end date year-month-day')
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
        _start_date = None
        if options.end_date:
            try:
                _end_date = datetime.datetime.strptime(options.end_date, "%Y-%m")
            except ValueError:
                # can't parse string, try with day as well
                _end_date = datetime.datetime.strptime(options.end_date, "%Y-%m-%d")
            print 'end_date=', _end_date
            params['end_date'] = _end_date
        params['mask'] = True
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
