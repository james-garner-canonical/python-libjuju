# Copyright 2023 Canonical Ltd.
# Licensed under the Apache V2, see LICENCE file for details.

from io import StringIO
from textwrap import indent


class CodeWriter(StringIO):
    """
    Blob of text that, when used in the context of facade.py, ends up
    holding the source code for a Python class and associated methods.

    """
    INDENT = "    "

    CLASS = 0
    METHOD = 1

    def write(self, msg, depth=0):
        if depth:
            prefix = self.INDENT * depth
            msg = indent(msg, prefix)

        return super(CodeWriter, self).write(msg)

    def __str__(self):
        return super(CodeWriter, self).getvalue()
