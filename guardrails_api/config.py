"""
All guards defined here will be initialized, if and only if
the application is using in memory guards.

The application will use in memory guards if pg_host is left
undefined. Otherwise, a postgres instance will be started
and guards will be persisted into postgres. In that case,
these guards will not be initialized.
"""
