import threading
import os
from functools import wraps


class RTWProtocolError(Exception):
    pass


def RTW(sources: list, destination_dir, n_lines=1):
    """
    RTW [read-transform-write] decorator will use the decorated function
        as a transformator function for lines read from a source data.
    The decorated function must be designed so:
     -it accepts a single argument - a text line [read from an open data iterator],
     -it returns a single line ended with a '\n' sign [to be saved in a destination data]
    RTW returns a wrapper that will not accept any argument. Once it is called (without any argument) it will:
    - start separate threading.Thread for every source data:
    - start reading lines from the source data , transforming and saving them to the destination data.
    - will return working processes in a list [so the threading.Thread.join method can be used later]
    Reading and writing is lazy - so it will not impinge memory unless to many existing_files are attempted to be opened.
    The destination existing_files will have the same name as the source existing_files - but will be placed in the destination directory.

    RTW arguments:
    - sources: list - a list of absolute paths to source existing_files
    - destination_dir - a directory for the destination existing_files to be saved in
    - n_lines: int =- a number of lines to be read and transformed as a batch before writing to a data.
    (Writing to a data is time expensive, so it pays to write once in a while in batches BUT
    reading many lines at the same time is memory consuming - best performance setting must be done by trials)

    WARNING:
        for the decorator to work, the sources [filenames] and destination_dir must be known at the decoration time \
        and those are usually known only at runtime - in that case this decorator might be useless.

    """

    def worker_fn(sfile_name, dfile_name, tform, nl):
        threading.local()._finished = False
        with open(sfile_name, 'r') as sfile:
            with open(dfile_name, 'w') as dfile:
                exit_flag = False
                while not exit_flag:
                    nli = 0
                    lines = list()
                    # loop reads lines from a source data
                    while nli < nl:
                        try:
                            lines.append(next(sfile))
                            nli += 1
                        except StopIteration:
                            exit_flag = True
                        finally:  # transformation of lines
                            lines = tuple(tform(line) for line in lines)
                    if lines:
                        if not all(line.endswith('\n') for line in lines):
                            raise RTWProtocolError(r'function must return a string line ending with a "\n" sign')
                        else:
                            lines = ''.join(lines)
                            dfile.write(lines)
                    else:
                        exit_flag = True
        threading.local()._finished = True
        return True

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if args or kwargs:
                raise RTWProtocolError('decorated function must be called without arguments')
            destination_filenames = (os.path.join(destination_dir, os.path.basename(spath)) for spath in sources)
            n_agents = len(sources)
            args_collection = tuple(zip(sources, destination_filenames, [fn] * n_agents, [n_lines] * n_agents))
            processes = [threading.Thread(target=worker_fn, args=args) for args in args_collection]
            [process.start() for process in processes]
            return processes
        return wrapper
    return decorator