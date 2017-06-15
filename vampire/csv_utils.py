import csv
import os

def add_field(table_name, new_field, value, type='DATE'):
    base,ext = os.path.splitext(table_name)
    if ext == '.csv':
        _new_csv = []
        with open(table_name, 'rb') as cf:
            _reader = csv.reader(cf)
            _header_row = next(_reader)
            _header_row.append(new_field)
            for row in _reader:
                _new_row = row
                _new_row.append(value)
                print _new_row
                _new_csv.append(_new_row)
        with open(table_name, 'wb') as wf:
            wr = csv.writer(wf)
            wr.writerow(_header_row)
            wr.writerows(_new_csv)
    return None

def calc_field(table_name, new_field, cal_field, multiplier=1.0, type='DOUBLE'):
    base,ext = os.path.splitext(table_name)
    if ext == '.csv':
        _new_csv = []
        with open(table_name, 'rb') as cf:
            _reader = csv.reader(cf)
            _header_row = next(_reader)
            _header_row.append(new_field)
            _calc_index = 0
            try:
                _calc_index = _header_row.index(cal_field.lower())
            except ValueError, e:
                print '{0} not found in file header row.'.format(cal_field)
                return None
            for row in _reader:
                _new_row = row
                if row[_calc_index] != '':
                    _val = float(row[_calc_index])
                    _new_row.append(int(_val*multiplier))
                else:
                    _new_row.append('')
                print _new_row
                _new_csv.append(_new_row)
        with open(table_name, 'wb') as wf:
            wr = csv.writer(wf)
            wr.writerow(_header_row)
            wr.writerows(_new_csv)
    return None

def csv_to_choropleth_format(input_filename, output_filename, area_field, value_field, start_date_field, end_date_field):
    _new_csv = []
    with open(input_filename, 'rb') as cf:
        _reader = csv.reader(cf)
        _header_row = next(_reader)
        _new_header_row = ['area_id', 'value', 'start_date', 'end_date']
        _area_index = 0
        _value_index = 0
        _start_date_index = 0
        _end_date_index = 0
        try:
            _area_index = _header_row.index(area_field)
            _value_index = _header_row.index(value_field)
            _start_date_index = _header_row.index(start_date_field)
            _end_date_index = _header_row.index(end_date_field)
        except ValueError, e:
            print 'Field name not found in file header row.', e
            return None

        for row in _reader:
            _new_row = []
            _new_row.append(row[_area_index])
            _new_row.append(row[_value_index])
            _new_row.append(row[_start_date_index])
            _new_row.append(row[_end_date_index])
            print _new_row
            _new_csv.append(_new_row)
    with open(output_filename, 'wb') as wf:
        wr = csv.writer(wf)
        wr.writerow(_new_header_row)
        wr.writerows(_new_csv)
    return output_filename