import csv
import os
import dbfpy.dbf
import pandas

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
#                print _new_row
                _new_csv.append(_new_row)
        with open(table_name, 'wb') as wf:
            wr = csv.writer(wf)
            wr.writerow(_header_row)
            wr.writerows(_new_csv)
    return None

def copy_field(table_name, new_field, copy_field):
    base,ext = os.path.splitext(table_name)
    if ext == '.csv':
        _new_csv = []
        with open(table_name, 'rb') as cf:
            _reader = csv.reader(cf)
            _header_row = next(_reader)
            _header_row.append(new_field)
            _lower_header = [x.lower() for x in _header_row]
            _lower_header = [x.replace("\'", "") for x in _lower_header]
            _calc_index = 0
            try:
                _calc_index = _lower_header.index(copy_field.lower())
            except ValueError, e:
                print '{0} not found in file header row.'.format(copy_field)
                return None
            for row in _reader:
                _new_row = row
                _new_row.append(row[_calc_index])
#                print _new_row
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
            # convert all to lower case for comparison
            _lower_header = [x.lower() for x in _header_row]
            _lower_header = [x.replace("\'", "") for x in _lower_header]
            _calc_index = 0
            try:
                _calc_index = _lower_header.index(cal_field.lower())
            except ValueError, e:
                print '{0} not found in file header row.'.format(cal_field)
                return None
            for row in _reader:
                _new_row = row
                if row[_calc_index] != '':
                    _val = float(row[_calc_index])
                    if type == 'LONG':
                        _new_row.append(int(_val*multiplier))
                    else:
                        _new_row.append(float(_val*multiplier))
                else:
                    _new_row.append('')
 #               print _new_row
                _new_csv.append(_new_row)
        with open(table_name, 'wb') as wf:
            wr = csv.writer(wf)
            wr.writerow(_header_row)
            wr.writerows(_new_csv)
    return None

def calc_pc_field(table_name, new_field, numerator_field, denominator_field):
    base,ext = os.path.splitext(table_name)
    if ext == '.csv':
        _new_csv = []
        with open(table_name, 'rb') as cf:
            _reader = csv.reader(cf)
            _header_row = next(_reader)
            _header_row.append(new_field)
            # convert all to lower case for comparison
            _lower_header = [x.lower() for x in _header_row]
            _num_index = 0
            _den_index = 0
            try:
                _num_index = _lower_header.index(numerator_field.lower())
            except ValueError, e:
                print '{0} not found in file header row.'.format(numerator_field)
                return None
            try:
                _den_index = _lower_header.index(denominator_field.lower())
            except ValueError, e:
                print '{0} not found in file header row.'.format(denominator_field)
                return None
            for row in _reader:
                _new_row = row
                if row[_num_index] != '':
                    _num_val = float(row[_num_index])
                    if row[_den_index] != '':
                        _den_val = float(row[_den_index])
                        if type == 'LONG':
                            _new_row.append(int(_num_val/_den_val*100))
                        else:
                            _new_row.append(float(_num_val/_den_val*100.0))
                    else:
                        _new_row.append('')
                else:
                    _new_row.append('')
#                print _new_row
                _new_csv.append(_new_row)
        with open(table_name, 'wb') as wf:
            wr = csv.writer(wf)
            wr.writerow(_header_row)
            wr.writerows(_new_csv)
    return None

def calc_normalized_field(table_name, new_field, area_field, total_field, admin_area):
    base,ext = os.path.splitext(table_name)
    if ext == '.csv':
        _df = pandas.read_csv(table_name) #, dtype={'dsd_code':'str'})
        _df['dsd_code'] = _df['DSD_C'].map('{:.0f}'.format)
        _df[new_field] = 0.0
        _df = pandas.merge(_df, admin_area[['dsd_code', 'shape_Area']], on='dsd_code', how='left')

        def new_value_formula(area, total, shape_area):
            return (area / total) * (total / (shape_area/10000.0)) * 100.0
        _df[new_field] = _df.apply(lambda row: new_value_formula(row[area_field], row[total_field],
                                                                 row['shape_Area']), axis=1)
#        for index,row in _df.iterrows():
#            _admin_row = admin_area.loc[(admin_area['dsd_code'] == str(int(row['dsd_code'])))]
##            row[new_field] = (row[area_field] / row[total_field] ) * (row[total_field] / (_admin_row['shape_Area']/10000.0)) * 100.0
#            _df.loc[index, new_field] = (row[area_field] / row[total_field] ) * (row[total_field] / (_admin_row['shape_Area']/10000.0)) * 100.0
        _min_area_aff = _df[area_field].min()
        _max_area_aff = _df[area_field].max()
        _min_total_area = _df[total_field].min()
        _max_total_area = _df[total_field].max()
        _df['impact_norm2'] = ((_df[area_field] - _min_area_aff) / (_max_area_aff - _min_area_aff)) / (
            (_df[total_field] - _min_total_area) / (_max_total_area - _min_total_area))
        _df['impact_norm2'] = _df['impact_norm2'].abs() * 100.0
##        print _df
        _df.to_csv(table_name)
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

import json
def convert_dbf_to_csv(input_dbf, output_csv):
    with open(output_csv, 'wb') as csv_file:
        _dbf_file = dbfpy.dbf.Dbf(input_dbf)
#        _out_csv = csv.writer(csv_file, quotechar="'", quoting=csv.QUOTE_NONNUMERIC)
        _out_csv = csv.writer(csv_file, quotechar='', quoting=csv.QUOTE_NONE)
        _header = []
        for field in _dbf_file.header.fields:
            _header.append(field.name)
        _out_csv.writerow(_header)
        for rec in _dbf_file:
            _out_csv.writerow(rec.fieldData)
        _dbf_file.close()
    # with open(output_csv, 'rb') as incsv:
    #     _csv_reader = csv.reader(incsv)
    #     with open(os.path.join(os.path.dirname(output_csv), "test.csv"), 'wb') as ocsv:
    #         _out_writer = csv.writer(ocsv, quotechar='', quoting=csv.QUOTE_NONE)
    #         for row in _csv_reader:
    #             _row = [s.replace("'", '"') if type(s) is str else s for s in row]
    #             _out_writer.writerows(row)
    return None

def merge_files(file1, file2, output_file, file1_field, file2_field):
    _first = pandas.read_csv(file1)
    _second = pandas.read_csv(file2)

    _merged = pandas.merge(_first, _second, how='inner', left_on=file1_field, right_on=file2_field)
    _merged.to_csv(output_file, index=False)

    return None

def aggregate_on_field(input, ref_field, output_fields_dict, output, all_fields=True):
    _input = pandas.read_csv(input)
    # create dictionary
    if all_fields:
        _fields_dict = {}
        _all_fields = _input.columns.values.tolist()
        for f in _all_fields:
            if not output_fields_dict.has_key(f):
                _fields_dict[f] = 'first'
            else:
                _fields_dict[f] = output_fields_dict[f]
    else:
        _fields_dict = output_fields_dict
    _result = _input.groupby(ref_field).agg(_fields_dict)
    _result.to_csv(output, index=False)
    return None
