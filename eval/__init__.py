import importlib, sys
_real_pkg = importlib.import_module('callguard.eval')
sys.modules[__name__] = _real_pkg
