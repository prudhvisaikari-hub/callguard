# Proxy package to expose internal CallGuard application as top-level `app`
import importlib, sys

_real_pkg = importlib.import_module('callguard.app')
sys.modules[__name__] = _real_pkg

_submodules = ['main', 'engine', 'nlp', 'stt', 'store', 'classifier', 'llm', 'symphony']
for _sub in _submodules:
    try:
        mod = importlib.import_module(f'callguard.app.{_sub}')
        sys.modules[f'{__name__}.{_sub}'] = mod
    except Exception:
        pass
