from . import modules
from . import core
from .core import CHECFiles, SubmitPluginBase
from .core import importdir as _import
import os as _os
from .utils import get_root_folder as _get_root_folder
_import.do(_os.path.join(_get_root_folder(), "crundb", "modules"), globals())