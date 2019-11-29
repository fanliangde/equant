
# -*- coding: utf-8 -*-
import re
import sys
import os

path = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.abspath(path))

import platform
from equant import main
from equant import excepthook_


if __name__ == '__main__':
    sys.excepthook = excepthook_
    # ------------任务栏显示app的图标-----------------
    if 'Windows' == platform.system():
        import ctypes
        myappid = 'equant.ui.view.QuantApplication'  # app路径
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # ------------------------------------------------
    main()
