from guardrails_api_client import Guard
from guardrails_api.clients.memory_guard_client import MemoryGuardClient
from guardrails_api.clients.pg_guard_client import PGGuardClient
from guardrails_api.clients.postgres_client import postgres_is_enabled


guard_client = None


def get_guard_client():
    global guard_client

    if not guard_client:
        # if no pg_host is set, use in memory guards
        if postgres_is_enabled():
            guard_client = PGGuardClient()
        else:
            guard_client = MemoryGuardClient()
            # Will be defined at runtime
            from guardrails_api import config

            exports = config.__dir__()
            for export_name in exports:
                export = getattr(config, export_name)
                is_guard = isinstance(export, Guard)
                if is_guard:
                    guard_client.create_guard(export)

    return guard_client
