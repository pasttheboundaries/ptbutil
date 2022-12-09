import os
import site
from ptbutil.iteration import flatlist


def available_sitepackages():
    return sorted(flatlist([os.listdir(dir_) for dir_ in  site.getsitepackages()]))
