from crundb.core import importdir
from crundb.utils import get_root_folder,get_data_folder
import os
import yaml
import re
from collections import defaultdict
class CHECFiles:

    """Summary
    """

    def __init__(self):
        """Summary
        """
        with open(os.path.join(get_data_folder(),'pageconf.yaml')) as f:
            conf = yaml.load(f)
        self._file_def = conf['FileDefs']
        self._file_collection = {'Run':None}
        for key in self._file_def.keys():
               self._file_collection[key] = None
        self._has_file_types = set()
        self._runs_file_collection = defaultdict(dict)
        self._counters = defaultdict(int)

    def classify_files(self, files):
        """Summary

        Args:
            files (TYPE): Description
        """
        for full_path in files:
            file = os.path.basename(full_path)
            if file[:3] == 'Run' and file[3]!='_':
                match= re.search(r'[0-9]+', file)
                span = match.span()
                runnumber = file[span[0]:span[1]]
                run_name = f"Run{runnumber}"
                if run_name not in  self._runs_file_collection:
                    self._runs_file_collection[run_name] ={'Run':run_name}
                    for fdef in self._file_def.keys():
                        self._runs_file_collection[run_name][fdef] = None
                tmp = defaultdict(list)
                for fdef,patrns in self._file_def.items():
                    for patrn in patrns:
                        if re.sub('\*',run_name,patrn) == file:
                            tmp[fdef].append(full_path)
                            self._counters[fdef] +=1
                # else:
                #     #Do something with unmatched files
                #     pass

                self._runs_file_collection[run_name].update(tmp)

            else:
                print("unknown format of file at location {}".format(full_path))
        return self._runs_file_collection

    def find_run_files(self,folder, run):
        """Summary

        Args:
            run (TYPE): Description
        """
        pass

class SubmitPluginBase:

    """Summary

    Attributes:
        subclasses (list): Description
    """

    subclasses = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for required in ("short_name",):
            if not getattr(cls, required):
                raise TypeError(
                    f"Can't instantiate abstract class {cls.__name__} without {required} attribute defined"
                )
        cls.subclasses.append(cls)

    def generate_submit(self, files):
        """Summary

        Args:
            files (TYPE): Description

        Raises:
            NotImplemented: Description
        """
        raise NotImplemented



