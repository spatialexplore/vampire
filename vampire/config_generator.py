import errno
import MODISConfigFactory
import CHIRPSConfigFactory

def generate_config_file(output_file, params):
    try:
        pfile = open(output_file, 'a')
    except IOError as e:
        if e.errno == errno.EACCES:
            return "Error creating file " + output_file
        # Not a permission error.
        raise
    else:
        with pfile:
            cf = CHIRPSConfigFactory.CHIRPSConfigFactory(name='cf')
            mf = MODISConfigFactory.MODISConfigFactory(name='mf', country=params['country'],
                                                       start_date=params['start_date'], end_date=None)
            pfile.write(cf.generate_header_directory())
            if 'product' in params:
                if params['product'] == "rainfall anomaly":
                    print "Not currently supported"
                    # pfile.write(self.generate_header_chirps())
                    # pfile.write(self.generate_header_run())
                    # pfile.write(self.generate_rainfall_anomaly_config(params['country'], params['interval'],
                    #                                                params['start_date'], params['output']))
                elif params['product'] == "vhi":
                    pfile.write(mf.generate_header_run())
#                    pfile.write(mf.generate_vci_config(params['country'], params['interval'],
#                                                       params['start_date'], params['output']))
                    pfile.write(mf.generate_tci_config(params['country'], params['interval'],
                                                       params['start_date'], params['output']))
#                    pfile.write(mf.generate_vhi_config(params['country'], params['interval'],
#                                                       params['start_date'], params['output']))
                elif params['product'] == "rainfall_longterm_average":
                    pfile.write(cf.generate_header_chirps())
                    pfile.write(cf.generate_header_run())
                    pfile.write(cf.generate_rainfall_long_term_average_config(params['country'],
                                                                                params['interval']
                                                                                ))
            pfile.close()
    return 0
