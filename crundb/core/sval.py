import math

def get_si_prefix(value: float,prefix=None,round_=True) -> tuple:
    """Summary

    Args:
        value (float): Description
        prefix (None, optional): Description
        round_ (bool, optional): Description

    Returns:
        tuple: Description
    """


    prefixes = [
        "a",
        "f",
        "p",
        "n",
        "μ",
        "m",
        "",
        "k",
        "M",
        "G",
        "T",
        "P",
        "E",
        "Z",
        "Y",
    ]
    if abs(value) < 1e-18:
        return 0, ""
    n = 0
    if prefix is None:
        i = int(math.floor(math.log10(abs(value))))
        i = int(i / 3)
    elif prefix == '':
        i = 0
        n = 1
    else:
        p = ' '.join(prefixes)
        i = (p.find(prefix)+1)//2-6
        n = 1
    p = math.pow(1000, i)
    ind = i + 6
    if round_:
        if isinstance(value,int):
            s = round(value / p, 1+n)
        else:
            s = round(value / p, 2+n)
    else:
        s = value
        ind = 6

    if s - int(s) == 0:
        s = int(s)
    #  if ind<0:
    #     ind = 0
    # if ind>14:
    #     ind=14
    return s, prefixes[ind]


class SVal:
    def __init__(self, value,unit='',stickyprefix=None,force=False,format_=True):
        self.value = value
        self.unit = unit
        self.stickyprefix = stickyprefix
        self.force = force
        self.type = type(value)
        self.format = format_
    def __repr__(self):
        if self.format:
            s = "{}{}{}".format(*get_si_prefix(self.value,self.stickyprefix),self.unit)
        else:
            s = f"{self.value}"
        return s


