import datetime
import calendar
import re

def _get_month_from_day_of_year(doy, year):
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy)
    month = '%s'%date.strftime('%m')
    return month

def _get_day_from_day_of_year(doy, year, ignore_leap_year = True):
    if calendar.isleap(year) and ignore_leap_year and doy > 60:
        doy = doy-1
    date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy-1)
    day = '%s'%date.strftime('%d')
    return day

def generate_output_filename(input_filename, in_pattern, out_pattern, ignore_leap_year= True, logger=None):
    _r_in = re.compile(in_pattern)
    _m = _r_in.match(input_filename)
    # get named parameters from output
    params = re.findall('{\w+}', out_pattern)
    # create new dictionary with parameter and value pairs
    ddict = {}
    if not _m:
        new_filename = input_filename
    else:
        for i in params:
            k = i[1:-1] # remove {}
            if k in _m.groupdict():
                ddict[k] = _m.groupdict()[k]
            else:
                # check if need to convert day of year into month, day
                if k == 'month' and 'dayofyear' in _m.groupdict():
                    ddict[k] = str(_get_month_from_day_of_year(int(_m.groupdict()['dayofyear']), int(_m.groupdict()['year']))).zfill(2)
                elif k == 'day' and 'dayofyear' in _m.groupdict():
                    ddict[k] = str(_get_day_from_day_of_year(int(_m.groupdict()['dayofyear']), int(_m.groupdict()['year']), ignore_leap_year)).zfill(2)
                else:
                    ddict[k] = "" # empty string as default
        new_filename = out_pattern.format(**ddict)
    if logger:
        logger.debug("old_filename: %s", input_filename)
        logger.debug("new_filename: %s", new_filename)
    return new_filename
