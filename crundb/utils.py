import os
import crundb
import datetime
import sys, os, time, atexit
from signal import SIGTERM
import errno

import io
import yaml
from collections import defaultdict
import re
import glob

def get_root_folder()->str:
    """Summary

    Returns:
        str: absolute path to project root
    """
    return os.path.dirname(os.path.dirname(crundb.__file__))


def get_dbdisplay_folder()->str:
    """Summary

    Returns:
        str: absolute path to dbdisplay folder
    """
    return os.path.join(get_root_folder(), "dbdisplay")


def get_data_folder()->str:
    """Summary

    Returns:
        str: absolute path to data folder
    """
    return os.path.join(get_root_folder(), "data")


def nested_access(d:dict, *keys):
    """Summary

    Args:
        d (TYPE): Description
        *keys: Description

    Returns:
        TYPE: Description
    """
    r = d
    for k in keys:
        r = r[k]
    return r


def printNiceTimeDelta(dt: datetime.timedelta)->str:
    """Summary

    Args:
        dt (datetime.timedelta): Description

    Returns:
        str: Description
    """
    if dt.days > 0:
        out = str(dt).replace(" days, ", ":")
    else:
        out = str(dt)
    outAr = out.split(":")
    outAr = ["%02d" % (int(float(x))) for x in outAr]
    out = ":".join(outAr)
    return out


def update_nested_dict(d:dict, path:str, type_:type, fun):
    """Summary

    Args:
        d (dict): Description
        path (str): Description
        type_ (type): Description
        fun (TYPE): Description
    """
    obj = d
    key_list = path.split(".")
    for k in key_list[:-1]:
        obj = obj[k]
    if isinstance(obj[key_list[-1]], type_):
        obj[key_list[-1]] = fun(obj[key_list[-1]])

from matplotlib.figure import Figure
def savefig_to_buffer(fig:Figure)->bytes:
    """Summary

    Args:
        fig (Figure): Description

    Returns:
        bytes: Description
    """
    figbuf = io.BytesIO()
    fig.savefig(figbuf, format="png")
    figbuf.seek(0)
    return figbuf.read()




class RunFilesRecord:
    def __init__(self,run,filedefs,**kwargs):
        """Summary

        Args:
            run (TYPE): Description
            filedefs (TYPE): Description
            **kwargs: Description
        """
        self._record = defaultdict(lambda: None)

        self._run = run
        for k in filedefs.keys():
            setattr(self,k,None)
            self._record[k] = None
        for k,v in kwargs.items():
            self._record[k] = [v]

    @property
    def run(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._run

    def __getitem__(self,key):
        return self._record[key]

    def items(self):
        return self._record.items()

    def update(self, d):
        for k,v in d.items():
            if v is None:
                continue
            if self._record[k]is not None:
               self._record[k] += v
            else:
                self._record[k] = v

        for k,v in self._record.items():
            setattr(self,k,v)
    def __str__(self):
        s =f"<RunFilesRecord>:\n{self._run}"
        for k,v in self._record.items():
            if v is not None:
                s +=f'\n{k}: {v}'
        return s

class RunFilesCollection:

    """Summary
    """

    def __init__(self):
        """Summary
        """
        self._collection ={}
        self._counters = defaultdict(int)

    def add(self,record):
        """Summary

        Args:
            record (TYPE): Description
        """
        if record.run in self._collection:
            self._collection[record.run].update(record)
        else:
            self._collection[record.run] =record
        for k,v in record.items():
            if v is not None:
             self._counters[k] +=1
    def items(self):
        return self.collection.items()

    @property
    def collection(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._collection

    @property
    def counters(self):
        """Summary

        Returns:
            TYPE: Description
        """
        return self._counters

def classify_files(files,filename_conf=os.path.join(get_data_folder(),'pageconf.yaml')):
    """Summary

    Args:
        files (TYPE): Description
    """
    with open(filename_conf) as f:
            conf = yaml.load(f)
    file_def = conf['FileDefs']
    collection = RunFilesCollection()


    for full_path in files:
        file = os.path.basename(full_path)
        if file[:3] == 'Run' and file[3]!='_':
            match= re.search(r'[0-9]+', file)
            span = match.span()
            runnumber = file[span[0]:span[1]]
            run_name = f"Run{runnumber}"

            for fdef,patrns in file_def.items():
                for patrn in patrns:
                    if re.sub('\*',run_name,patrn) == file:
                        collection.add(RunFilesRecord(run=run_name,filedefs = file_def,**{fdef:full_path}))
            # else:
            #     #Do something with unmatched files
            #     pass

        else:
            print("unknown format of file at location {}".format(full_path))
    return collection


def classify_files_r(folders:list or str,filename_conf:str=os.path.join(get_data_folder(),'pageconf.yaml')):
    """Summary

    Args:
        folders (list or str): Description
        filename_conf (str, optional): Description

    Returns:
        TYPE: Description
    """
    folders = []
    files = []
    if isinstance(folders,str):
        folders = [folders]
    for folder in folders:
        dir_structure = glob.glob(folder+'/**',recursive=True)
        for f in dir_structure:
            if os.path.isfile(f):
                files.append(f)
            if os.path.isdir(f):
                folders.append(f)
    return classify_files(files,filename_conf=filename_conf)

def pid_exists(pid: int)->bool:
    """Check whether pid exists in the current process table.
    UNIX only.

    Args:
        pid (int): Description

    Returns:
        bool: Description

    Raises:
        ValueError: Description
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError("invalid PID 0")
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(
        self, pidfile, stdin="/dev/null", stdout="/dev/null", stderr="/dev/null"
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, "r")
        so = open(self.stdout, "a+")
        se = open(self.stderr, "a+")
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, "w+").write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def getpid(self):
        pf = open(self.pidfile, "r")
        pid = int(pf.read().strip())
        if pid_exists(pid):
            return pid
        else:
            return None

    def start(self, daemonize=True):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, "r")
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = -1

        if pid_exists(pid):
            message = "pid %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        if daemonize:
            self.daemonize()
        else:
            # No redirect of standard file descriptors
            pass
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile, "r")
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
