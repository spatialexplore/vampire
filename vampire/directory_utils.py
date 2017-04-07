import os
import gzip
import regex

def get_matching_files(base_dir, pattern, logger=None):
    file_list = []
    if os.path.exists(base_dir):
        _all_files = os.listdir(base_dir)
        if not _all_files and logger is not None:
            logger.debug('No files in %s', base_dir)
        for f in _all_files:
            pth = os.path.join(base_dir, f)
            if not os.path.isdir(pth):
                # check file against filter pattern
                if regex.match(pattern, f):
                    file_list.append(pth)
        if not file_list and logger is not None:
            logger.debug('No files in %s match %s', base_dir, pattern)
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
