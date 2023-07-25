import importlib
from os import getcwd
from typing import Callable, List, Optional
from src.classes.guard_struct import GuardStruct
from src.utils.pip import install, is_frozen, uninstall, get_module_name
from src.utils.logger import logger

def dynamic_import(package: str):
    # We can't try to retrive the module name until the package is installed.
    # If it is already installed this will go quickly.
    package_path = f"{getcwd()}/{package}" if package == "guardrails-custom-validators" else package
    inst_out = install(package_path)
    logger.debug(inst_out)
    module_name = get_module_name(package)
    try:
        mod = importlib.import_module(module_name, package)
        return mod
    except Exception as e:
        logger.error(f"Failed to import {module_name}!", e)

def prep_environment(guard: GuardStruct):
    plugins: List[str] = guard.railspec.get_all_plugins()
    for p in plugins:
      dynamic_import(p)

def cleanup_environment(guard: GuardStruct):
    plugins: List[str] = guard.railspec.get_all_plugins()
    for p in plugins:
      # Only uninstall packages that we did not already have installed.
      logger.debug(f"checking if {p} is in requirements.txt")
      if is_frozen(p) is not True:
        logger.debug(f"uninstalling {p}")
        uninstall(p)