from . import importdir as _import
import os as _os
from crundb.utils import get_root_folder as _get_root_folder


class SubmitPluginBase:

    """Summary

    Attributes:
        subclasses (list): Description
    """

    subclasses = []
    _names = []
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for required in ("short_name",):
            if not getattr(cls, required):
                raise TypeError(
                    f"Can't instantiate abstract class {cls.__name__} without {required} attribute defined"
                )
        if cls.__class__ not in cls._names:
            cls.subclasses.append(cls)
            cls._names.append(cls.__class__)
        return cls

    def generate_submit(self, files):
        """Summary

        Args:
            files (TYPE): Description

        Raises:
            NotImplemented: Description
        """
        raise NotImplemented

class ServerSubmitPluginBase:

    """Summary

    Attributes:
        subclasses (list): Description
    """

    subclasses = []
    _names = []
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for required in ("short_name",):
            if not getattr(cls, required):
                raise TypeError(
                    f"Can't instantiate abstract class {cls.__name__} without {required} attribute defined"
                )

        if cls.__class__ not in cls._names:
            cls.subclasses.append(cls)
            cls._names.append(cls.__class__)
        return cls

    def generate_submit(self, args):
        """Summary

        Args:
            files (TYPE): Description

        Raises:
            NotImplemented: Description
        """
        raise NotImplemented

class ServerPluginBase:

    """Summary

    Attributes:
        subclasses (list): Description
    """

    subclasses = []
    _names = []
    def __init_subclass__(cls, **kwargs):

        super().__init_subclass__(**kwargs)
        for required in ("short_name",):
            if not getattr(cls, required):
                raise TypeError(
                    f"Can't instantiate abstract class {cls.__name__} without {required} attribute defined"
                )
        if cls.__class__ not in cls._names:
            cls.subclasses.append(cls)
            cls._names.append(cls.__class__)

    def generate_submit(self, files):
        """Summary

        Args:
            files (TYPE): Description

        Raises:
            NotImplemented: Description
        """
        raise NotImplemented

# import all plugins
_import.do(_os.path.join(_get_root_folder(), "crundb", "modules"), globals())
