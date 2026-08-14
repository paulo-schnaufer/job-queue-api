import os
import sys
from subprocess import Popen

worker = Popen([sys.executable, 'worker.py'])
api = Popen([
    sys.executable,
    '-m',
    'uvicorn',
    'app.main:app',
    '--host',
    '0.0.0.0',
    '--port',
    os.getenv('PORT', '8000'),
])

if worker.wait() != 0:
    api.terminate()
    raise SystemExit(worker.returncode)

if api.wait() != 0:
    worker.terminate()
    raise SystemExit(api.returncode)
