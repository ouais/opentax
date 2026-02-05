from .w2 import parse_w2
from .form_1099_int import parse_1099_int
from .form_1099_div import parse_1099_div
from .form_1099_b import parse_1099_b
from .form_1099_nec import parse_1099_nec

__all__ = [
    'parse_w2',
    'parse_1099_int',
    'parse_1099_div',
    'parse_1099_b',
    'parse_1099_nec',
]
