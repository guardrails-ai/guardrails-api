import sys
import subprocess
import pkg_resources as pkg
from os import getcwd
from typing import Optional, List
from src.utils import logger, get_file_contents


def pip_process(action: str, package: str, flags: Optional[List[str]] = []):
    try:
        logger.dev(f"running pip {action} {' '.join(flags)} {package}")
        command = [sys.executable, "-m", "pip", action]
        command.extend(flags)
        command.append(package)
        output = subprocess.check_output(command)
        logger.dev(f"decoding output from pip {action} {package}")
        return str(output.decode())
    except subprocess.CalledProcessError as exc:
        logger.error(
            f"Failed to {action} {package}",
            f"Exit code: {exc.returncode}",
            f"stdout: {exc.output}",
        )
    except Exception as e:
        logger.error(
            f"An unexpected exception occurred while try to {action} {package}!",
            e,
        )


def install(package):
    install_output = pip_process("install", package)
    logger.dev(install_output)


def uninstall(package):
    uninstall_output = pip_process("uninstall", package, ["-y"])
    logger.dev(uninstall_output)


def show(package):
    show_output = pip_process("show", package)
    logger.dev(show_output)


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
    logger.dev(f"{package} is frozen? {package_is_frozen}")
    return package_is_frozen


def get_module_name(package_name: str):
    module_name = package_name.replace("-", "_")  # a really bad fallback
    dist = pkg.get_distribution(package_name)
    if dist is not None:
        metadata_dir = dist.egg_info
        file_path = f"{metadata_dir}/top_level.txt"
        file = get_file_contents(file_path)
        if file is not None:
            module_name = file.read().rstrip().split("\n").pop(0)
    return module_name
