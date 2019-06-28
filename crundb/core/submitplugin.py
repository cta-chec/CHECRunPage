

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



