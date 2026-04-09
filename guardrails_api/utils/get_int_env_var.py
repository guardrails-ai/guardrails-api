import os


def get_int_env_var(name: str) -> int | None:
    value = os.getenv(name)
    if value:
        try:
            int_value = int(value)
            return int_value
        except ValueError:
            raise ValueError(
                f"Invalid value for environment variable {name}: {value}! {name} must be an integer!"
            )
