
# -*- coding: utf-8 -*-
import re
import sys
import os

import platform
from equant import main
from equant import excepthook_


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(equant-script\.pyw?|\.exe)?$', '', sys.argv[0])
    os.chdir(os.path.abspath(sys.argv[0]))

    sys.excepthook = excepthook_
    # ------------任务栏显示app的图标-----------------
    if 'Windows' == platform.system():
        import ctypes
        myappid = 'equant.ui.view.QuantApplication'  # app路径
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # ------------------------------------------------
    main()
