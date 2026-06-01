#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: blueprint_config
short_description: Collect rendered device configurations from an Apstra blueprint
version_added: "1.0.9"
author:
  - "Prabhanjan KV (@kvp_jnpr)"
description:
  - This module collects the rendered configuration from devices in an
    Apstra blueprint for external storage, backup, compliance auditing,
    or version control.
  - Configurations are retrieved per device via the
    C(/api/blueprints/{id}/nodes/{node_id}/config-rendering) API endpoint.
  - Supports filtering by device name, device role (spine, leaf, etc.),
    or an explicit list of device names.
  - Optionally saves rendered configs to local files (one file per device).
options:
  api_url:
    description:
      - The URL used to access the Apstra api.
    type: str
    required: false
  verify_certificates:
    description:
      - If set to false, SSL certificates will not be verified.
    type: bool
    required: false
    default: True
  username:
    description:
      - The username for authentication.
    type: str
    required: false
  password:
    description:
      - The password for authentication.
    type: str
    required: false
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  id:
    description:
      - Dictionary containing the blueprint identifier.
      - C(blueprint) is the blueprint ID or label.
    required: true
    type: dict
  devices:
    description:
      - List of device hostnames to collect configs for.
      - If omitted, configs are collected for all devices in the blueprint.
    required: false
    type: list
    elements: str
  role:
    description:
      - Filter devices by role.
      - Common roles include C(spine), C(leaf), C(superspine), C(access).
      - Cannot be used together with C(devices).
    required: false
    type: str
    choices: ["spine", "leaf", "superspine", "access"]
  output_dir:
    description:
      - Directory path to save rendered config files.
      - One file per device will be created.
      - Directory will be created if it does not exist.
    required: false
    type: str
  filename_pattern:
    description:
      - Pattern for output filenames when C(output_dir) is specified.
      - Supports C({hostname}) placeholder.
    required: false
    type: str
    default: "{hostname}.conf"
  state:
    description:
      - The action to perform.
      - C(collected) retrieves rendered configurations.
    required: false
    type: str
    choices: ["collected"]
    default: "collected"
requirements:
  - "python >= 3.10"
  - "aos-sdk >= 0.1.0"
"""

EXAMPLES = """
- name: Collect rendered config for all devices in a blueprint
  juniper.apstra.blueprint_config:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    auth_token: "{{ auth.token }}"
  register: result

- name: Collect config for specific devices
  juniper.apstra.blueprint_config:
    id:
      blueprint: "my-blueprint"
    devices:
      - spine1
      - leaf1
    auth_token: "{{ auth.token }}"
  register: result

- name: Collect config for all spine devices
  juniper.apstra.blueprint_config:
    id:
      blueprint: "my-blueprint"
    role: spine
    auth_token: "{{ auth.token }}"
  register: result

- name: Collect and save configs to files
  juniper.apstra.blueprint_config:
    id:
      blueprint: "my-blueprint"
    output_dir: "/tmp/configs"
    filename_pattern: "{hostname}.conf"
    auth_token: "{{ auth.token }}"
  register: result

- name: Collect configs for leaf devices and save to files
  juniper.apstra.blueprint_config:
    id:
      blueprint: "my-blueprint"
    role: leaf
    output_dir: "/tmp/leaf-configs"
    auth_token: "{{ auth.token }}"
  register: result
"""

RETURN = """
changed:
  description: Always false since this is a read-only module.
  type: bool
  returned: always
  sample: false
configs:
  description: >
    Dictionary of rendered configurations keyed by device hostname.
    Each entry contains the hostname, rendered config text, and NOS type.
  type: dict
  returned: always
  sample:
    spine1:
      hostname: "spine1"
      config: "set system host-name spine1..."
      system_id: "abc123"
      role: "spine"
    leaf1:
      hostname: "leaf1"
      config: "hostname leaf1..."
      system_id: "def456"
      role: "leaf"
device_count:
  description: Number of devices for which configs were collected.
  type: int
  returned: always
  sample: 4
files_written:
  description: >
    List of file paths written when output_dir is specified.
  type: list
  returned: when output_dir is specified
  sample: ["/tmp/configs/spine1.conf", "/tmp/configs/leaf1.conf"]
msg:
  description: Status message.
  type: str
  returned: always
"""

import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


def _get_system_nodes(base_client, blueprint_id, module):
    """
    List all system nodes in a blueprint using direct API.

    Returns a list of node dicts with id, hostname, role, etc.
    """
    url = f"/blueprints/{blueprint_id}/nodes?node_type=system"
    module.debug(f"Fetching system nodes from: {url}")
    response = base_client._request(url=url, method="GET")
    nodes = []
    if isinstance(response, dict):
        items = response.get("nodes", response)
        if isinstance(items, dict):
            for node_id, node_data in items.items():
                if isinstance(node_data, dict):
                    if "id" not in node_data:
                        node_data["id"] = node_id
                    nodes.append(node_data)
        elif isinstance(items, list):
            nodes = items
    elif isinstance(response, list):
        nodes = response
    return nodes


def _get_config_rendering(base_client, blueprint_id, node_id, module):
    """
    Get the rendered configuration for a specific node.

    Returns the rendered config string or dict.
    """
    url = f"/blueprints/{blueprint_id}/nodes/{node_id}/config-rendering"
    module.debug(f"Fetching config rendering from: {url}")
    response = base_client._request(url=url, method="GET")
    return response


def _filter_nodes(nodes, devices=None, role=None):
    """
    Filter nodes by device names or role.

    Args:
        nodes: List of node dicts.
        devices: Optional list of hostnames to include.
        role: Optional role string to filter by.

    Returns:
        Filtered list of node dicts.
    """
    filtered = []
    for node in nodes:
        hostname = node.get("hostname") or node.get("label") or ""
        node_role = node.get("role", "")

        if devices is not None:
            if hostname in devices:
                filtered.append(node)
        elif role is not None:
            if node_role == role:
                filtered.append(node)
        else:
            filtered.append(node)
    return filtered


def _write_config_file(output_dir, filename_pattern, hostname, config_text):
    """
    Write a rendered config to a file.

    Returns the file path written.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = filename_pattern.format(hostname=hostname)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(config_text)
    return filepath


def _extract_config_text(rendering_response):
    """
    Extract the config text from the rendering API response.

    The response format may vary; handle common formats.
    """
    if isinstance(rendering_response, str):
        return rendering_response
    if isinstance(rendering_response, dict):
        # Try common response keys
        for key in ["config", "content", "rendered_config", "configuration"]:
            if key in rendering_response:
                return rendering_response[key]
        # If there's a nested config object, return the whole dict as string
        return str(rendering_response)
    return str(rendering_response)


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        devices=dict(type="list", elements="str", required=False, default=None),
        role=dict(
            type="str",
            required=False,
            default=None,
            choices=["spine", "leaf", "superspine", "access"],
        ),
        output_dir=dict(type="str", required=False, default=None),
        filename_pattern=dict(type="str", required=False, default="{hostname}.conf"),
        state=dict(
            type="str", required=False, choices=["collected"], default="collected"
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False, configs={}, device_count=0)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[["devices", "role"]],
    )

    try:
        client_factory = ApstraClientFactory.from_params(module)

        id_param = module.params["id"]
        devices = module.params.get("devices")
        role = module.params.get("role")
        output_dir = module.params.get("output_dir")
        filename_pattern = module.params.get("filename_pattern")

        # Resolve blueprint name to ID
        blueprint_id = id_param.get("blueprint")
        if blueprint_id is None:
            raise ValueError("'blueprint' key is required in the 'id' parameter")
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)

        # Get the base client for direct API calls
        base_client = client_factory.get_base_client()

        # Fetch all system nodes in the blueprint
        all_nodes = _get_system_nodes(base_client, blueprint_id, module)
        module.debug(f"Found {len(all_nodes)} system nodes in blueprint {blueprint_id}")

        # Filter nodes based on devices or role
        target_nodes = _filter_nodes(all_nodes, devices=devices, role=role)
        module.debug(f"Targeting {len(target_nodes)} nodes after filtering")

        if devices is not None:
            # Validate all requested devices were found
            found_hostnames = {
                n.get("hostname") or n.get("label") or "" for n in target_nodes
            }
            missing = set(devices) - found_hostnames
            if missing:
                module.warn(
                    f"Requested devices not found in blueprint: {', '.join(sorted(missing))}"
                )

        configs = {}
        files_written = []

        for node in target_nodes:
            node_id = node.get("id")
            hostname = node.get("hostname") or node.get("label") or node_id
            node_role = node.get("role", "unknown")

            if not node_id:
                module.warn(f"Skipping node with no ID: {node}")
                continue

            module.debug(f"Collecting config for {hostname} (node_id={node_id})")

            try:
                rendering = _get_config_rendering(
                    base_client, blueprint_id, node_id, module
                )
                config_text = _extract_config_text(rendering)

                configs[hostname] = {
                    "hostname": hostname,
                    "config": config_text,
                    "system_id": node.get("system_id", ""),
                    "role": node_role,
                }

                # Write to file if output_dir is specified
                if output_dir is not None:
                    filepath = _write_config_file(
                        output_dir, filename_pattern, hostname, config_text
                    )
                    files_written.append(filepath)
                    module.debug(f"Wrote config for {hostname} to {filepath}")

            except Exception as e:
                module.warn(
                    f"Failed to collect config for {hostname} "
                    f"(node_id={node_id}): {str(e)}"
                )
                configs[hostname] = {
                    "hostname": hostname,
                    "config": None,
                    "system_id": node.get("system_id", ""),
                    "role": node_role,
                    "error": str(e),
                }

        result["configs"] = configs
        result["device_count"] = len(configs)
        result["msg"] = (
            f"Collected configs for {len(configs)} device(s) "
            f"from blueprint {blueprint_id}"
        )

        if output_dir is not None:
            result["files_written"] = files_written

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
