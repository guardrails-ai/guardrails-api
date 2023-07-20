import sys
import subprocess
import pkg_resources as pkg
from os import getcwd
from typing import Optional, List
from src.utils.logger import logger
from src.utils.file import get_file_contents

def pip_process(action: str, package: str, flags: Optional[List[str]] = []):
    try:
      logger.debug(f"running pip {action} {' '.join(flags)} {package}")
      command = [sys.executable, "-m", "pip", action]
      command.extend(flags)
      command.append(package)
      output = subprocess.check_output(command)
      logger.debug(f"decoding output from pip {action} {package}")
      return str(output.decode())
    except subprocess.CalledProcessError as exc:
      logger.error(f"Failed to {action} {package}", f"Exit code: {exc.returncode}", f"stdout: {exc.output}")
    except Exception as e:
      logger.error(f"An unexpected exception occurred while try to {action} {package}!", e)
       

def install(package):
  return pip_process("install", package)

def uninstall(package):
    return pip_process("uninstall", package, ["-y"])

def show(package):
   return pip_process("show", package)

def is_installed(package):
   show_output = pip_process("show", package)
   if show_output is None:
      return False
   else:
      return True

# Checks if a package is containd in the requirements.txt
def is_frozen(package):
    requirements_txt_path = f"{getcwd()}/requirements.txt"
    requirements = open(requirements_txt_path, "r")
    package_is_frozen = False
    for line in requirements:
      module_name = line.split("==").pop(0)
      module_name = module_name.split(" @ ").pop(0)
      if module_name == package:
          package_is_frozen = True
          break
    logger.debug(f"{package} is frozen? {package_is_frozen}")
    return package_is_frozen

def get_module_name(package_name: str):
    module_name = package_name.replace("-", "_") # a really bad fallback
    dist = pkg.get_distribution(package_name)
    if dist is not None:
      metadata_dir = dist.egg_info
      file_path = f"{metadata_dir}/top_level.txt"
      file = get_file_contents(file_path)
      if file is not None:
          module_name = file.read().rstrip().split('\n').pop(0)
    return module_name
         