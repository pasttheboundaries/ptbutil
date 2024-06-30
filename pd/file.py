import os
import re
import pandas as pd
from ptbutil.env import available_sitepackages

"""
functions that read csv, xls, xlsx existing_files
"""
VALID_EXTENTIONS = 'xls xlsx csv ods'.split()


def _detect_extentions_in_dir(directory):
    return tuple({f.split('.')[-1] for f in os.listdir(directory)})


def _find_user_indicated_files(directory, nameroot, extention):
    files = {f for f in os.listdir(directory)}

    if extention:
        files = {f for f in files if f.endswith(extention)}

    if nameroot:
        nr_re = re.compile(nameroot)
        files = {f for f in files if nr_re.search(f)}

    return sorted({os.path.join(directory, f) for f in files})

def _read_df_by_ex(extension, filepath, encoding='utf-8', sep=','):

    if extension == 'csv':
        return pd.read_csv(filepath, low_memory=False, encoding=encoding, sep=sep)
    elif extension in ('xls', 'xlsx'):
        return pd.read_excel(filepath)
    elif extension  == 'ods' and 'odf' in available_sitepackages():
        try:
            return pd.read_excel(filepath, engine="odf")
        except UnicodeDecodeError:
            with open(filepath, mode="rb") as excel_file:
                return pd.read_excel(excel_file)
    else:
        raise ValueError(f'Could not read data with extension {extension}')


def read_dir_files(directory=None, nameroot=None, extension=None, encoding='utf-8', sep=','):
    """
    Supports opening existing_files with extensions
    :param directory: str, if None existing_files will be read from current working directory
    :param nameroot: str - part of the filename that will qualify data to be read
    :param extension: str - extention of existing_files to be read.
    :return: a tuple of (list of pd.DataFrames, list of existing_files paths)
    """
    if extension and extension not in VALID_EXTENTIONS:
        raise ValueError(f'Invalid extension {extension}')
    directory = directory or os.getcwd()
    if any((nameroot, extension)):
        files = _find_user_indicated_files(directory, nameroot, extension)
        extensions = set([f.split('.')[-1] for f in files])
        if len(extensions) > 1:
            raise Exception('Detected multiple data extensions. Please specify 1 valid data extension or name root.')
        elif len(extensions) < 1:
            raise FileNotFoundError('No valid data extension found.')
        else:
            ex = extensions.pop()  # detected existing_files valid
    else:
        #directory = config.TARGET_DIR
        extention_in_dir = _detect_extentions_in_dir(directory)
        accepted_extensions = [ex for ex in extention_in_dir if ex in VALID_EXTENTIONS]
        if len(accepted_extensions) > 1:
            raise Exception('Detected multiple existing_files with valid extensions. Please specify data extension or name root.')
        elif len(accepted_extensions) < 1:
            raise FileNotFoundError('No valid existing_files found in current working directory.')
        else:
            ex = accepted_extensions.pop()
            files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(ex)]
    return [_read_df_by_ex(ex, f, encoding=encoding, sep=sep) for f in files], files
