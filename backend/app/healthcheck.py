"""Exit code para Docker; el heartbeat es independiente del éxito del proveedor."""

import sys
from .db import session_scope
from .config import settings
from .models import WorkerState, utcnow
from .provider import aware

with session_scope() as s:
    row = s.get(WorkerState, settings.mode)
    sys.exit(
        0
        if row
        and (utcnow() - aware(row.heartbeat)).total_seconds()
        < settings.worker_heartbeat_timeout
        else 1
    )
