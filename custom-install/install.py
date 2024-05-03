import os
import sys
import logging
import json
from typing import Any, Dict
from rich.console import Console
from guardrails.cli.hub.install import (
    get_site_packages_location,
    install_hub_module,
    run_post_install,
    add_to_hub_inits
)
from guardrails.cli.server.module_manifest import ModuleManifest
from string import Template

console = Console()

os.environ[
    "COLOREDLOGS_LEVEL_STYLES"
] = "spam=white,faint;success=green,bold;debug=magenta;verbose=blue;notice=cyan,bold;warning=yellow;error=red;critical=background=red"  # noqa
LEVELS = {
    "SPAM": 5,
    "VERBOSE": 15,
    "NOTICE": 25,
    "SUCCESS": 35,
}
for key in LEVELS:
    logging.addLevelName(LEVELS.get(key), key)  # type: ignore
logger = logging.getLogger("custom-install")


def load_manifest(fileName: str) -> Dict[str, Any]:
    with open(f"custom-install/manifests/{fileName}") as manifest_file:
        content = manifest_file.read()
        return json.loads(content)

custom_manifests = {
    "guardrails/provenance_llm": load_manifest("provenance-llm.json"),
    "guardrails/detect_pii": load_manifest("detect-pii.json"),
    "guardrails/competitor_check": load_manifest("competitor-check.json"),
   "guardrails/many_shot_jailbreak": load_manifest("jailbreak.json"),
}

def get_validator_manifest(module_name) -> ModuleManifest:
    manifest = custom_manifests.get(module_name, {})
    return ModuleManifest.from_dict(manifest)

def custom_install(package_uri: str):
    """Install a validator from the Hub."""
    if not package_uri.startswith("hub://"):
        logger.error("Invalid URI!")
        sys.exit(1)

    console.print(f"\nInstalling {package_uri}...\n")
    logger.log(
        level=LEVELS.get("SPAM"), msg=f"Installing {package_uri}..."  # type: ignore
    )

    # Validation
    module_name = package_uri.replace("hub://", "")

    # Prep
    with console.status("Fetching manifest", spinner="bouncingBar"):
        module_manifest = get_validator_manifest(module_name)
        site_packages = get_site_packages_location()

    # Install
    with console.status("Downloading dependencies", spinner="bouncingBar"):
        install_hub_module(module_manifest, site_packages)

    # Post-install
    with console.status("Running post-install setup", spinner="bouncingBar"):
        run_post_install(module_manifest, site_packages)
        add_to_hub_inits(module_manifest, site_packages)

    success_message_cli = Template(
        """✅Successfully installed ${module_name}!

[bold]Import validator:[/bold]
from guardrails.hub import ${export}

[bold]Get more info:[/bold]
https://hub.guardrailsai.com/validator/${id}
"""
    ).safe_substitute(
        module_name=package_uri,
        id=module_manifest.id,
        export=module_manifest.exports[0],
    )
    success_message_logger = Template(
        """✅Successfully installed ${module_name}!

Import validator:
from guardrails.hub import ${export}

Get more info:
https://hub.guardrailsai.com/validator/${id}
"""
    ).safe_substitute(
        module_name=package_uri,
        id=module_manifest.id,
        export=module_manifest.exports[0],
    )
    console.print(success_message_cli)  # type: ignore
    logger.log(level=LEVELS.get("SPAM"), msg=success_message_logger)  # type: ignore
    

custom_install("hub://guardrails/provenance_llm")
# custom_install("hub://guardrails/detect_pii")
# custom_install("hub://guardrails/competitor_check")
# custom_install("hub://guardrails/many_shot_jailbreak")
