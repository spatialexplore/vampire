import os
import gzip
import re

def get_matching_files(base_dir, pattern):
    file_list = []
    if os.path.exists(base_dir):
        _all_files = os.listdir(base_dir)
        for f in _all_files:
            pth = os.path.join(base_dir, f)
            if not os.path.isdir(pth):
                # check file against filter pattern
                if re.match(pattern, f):
                    file_list.append(pth)
    return file_list

def unzip_file_list(file_list):
    # TODO: need to check if unzipped file already exists
    newlist = []
    for f in file_list:
        if os.path.splitext(f)[1] == '.gz':
            with gzip.open(f, 'rb') as _in_file:
                s = _in_file.read()
            _path_to_store = os.path.splitext(f)[0] #f[:-3]
            with open(_path_to_store, 'wb') as _out_file:
                _out_file.write(s)
                newlist.append(_path_to_store)
        else:
            newlist.append(f)
    return newlist
