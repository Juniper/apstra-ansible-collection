#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: ztp_config

short_description: Manage ZTP VM configuration (DHCP, firmware, passwords)

version_added: "0.1.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module manages the Apstra ZTP VM configuration including DHCP
    host-reservations, subnets, pools, firmware mappings, and passwords.
  - The ZTP VM is a separate appliance from the Apstra server and requires
    its own connection parameters (C(ztp_url), C(ztp_username), C(ztp_password)).
  - Two configuration scopes are supported via the C(scope) parameter.
  - C(dhcp_configurator) manages DHCP subnets, pools, host-reservations,
    and global DHCP options via the C(/api/ztp/config/dhcp/configurator) endpoint.
  - C(ztp_config) manages firmware mappings, default passwords, and ZTP
    workflow settings via the C(/api/ztp/config/ztpjson) endpoint.
  - C(password) changes the ZTP web UI admin password via
    C(/api/ztp/aaa/change-password).
  - The module is idempotent — it reads the current configuration, compares
    it with the desired state, and only applies changes when differences exist.

options:
  ztp_url:
    description:
      - Base URL of the ZTP VM (e.g., C(https://10.204.22.128)).
      - Required because the ZTP VM is typically a separate appliance
        from the Apstra server.
      - Can also be set via the C(ZTP_URL) environment variable.
    type: str
    required: false
  ztp_username:
    description:
      - Username for ZTP VM authentication.
      - Can also be set via the C(ZTP_USERNAME) environment variable.
    type: str
    required: false
  ztp_password:
    description:
      - Password for ZTP VM authentication.
      - Can also be set via the C(ZTP_PASSWORD) environment variable.
    type: str
    required: false
  ztp_auth_token:
    description:
      - Pre-existing auth token for the ZTP VM.
      - Can also be set via the C(ZTP_AUTH_TOKEN) environment variable.
    type: str
    required: false
  ztp_verify_certificates:
    description:
      - Whether to verify SSL certificates when connecting to the ZTP VM.
    type: bool
    required: false
    default: false
  scope:
    description:
      - The configuration scope to manage.
      - C(dhcp_configurator) — manage DHCP subnets, pools, host-reservations,
        and DHCP options.
      - C(ztp_config) — manage firmware mappings, default passwords, and
        ZTP workflow settings.
      - C(password) — change the ZTP web UI admin password.
    type: str
    required: true
    choices:
      - dhcp_configurator
      - ztp_config
      - password
  state:
    description:
      - Desired state of the configuration.
      - C(present) — create or update the configuration to match the
        desired state.
      - C(absent) — remove specific items (host-reservations, subnets).
        Only applicable for C(dhcp_configurator) scope.
      - C(query) — retrieve the current configuration without making
        changes.
    type: str
    required: false
    choices:
      - present
      - absent
      - query
    default: present
  subnets:
    description:
      - List of subnet definitions for DHCP configuration.
      - Each subnet must include C(subnet) (CIDR notation), C(router)
        (gateway IP), and C(pools) (list of IP ranges).
      - Used with C(scope=dhcp_configurator).
    type: list
    elements: dict
    required: false
  host_reservations:
    description:
      - List of MAC-to-IP host reservations for DHCP.
      - Each entry must include C(hw-address) (MAC address) and
        C(ip-address) (IP to assign).
      - Optional C(hostname) for the reservation.
      - Used with C(scope=dhcp_configurator).
    type: list
    elements: dict
    required: false
  global_host_reservations:
    description:
      - List of global (outside-subnet) host reservations.
      - Same format as C(host_reservations).
      - Used with C(scope=dhcp_configurator).
    type: list
    elements: dict
    required: false
  options:
    description:
      - DHCP options to set globally.
      - Supported keys include C(domain-name), C(domain-search),
        C(domain-name-servers) (list of IPs), C(tftp-server-name).
      - Used with C(scope=dhcp_configurator).
    type: dict
    required: false
  reservation_mode_default:
    description:
      - Default reservation mode for DHCP.
      - Valid values are C(all), C(global), C(out-of-pool), C(disabled).
      - Used with C(scope=dhcp_configurator).
    type: list
    elements: str
    required: false
  firmware:
    description:
      - Firmware/ZTP configuration data (the full ZTP JSON config dict).
      - This is the content of the ZTP JSON configuration, keyed by
        platform (e.g., C(defaults), C(junos), C(nxos), C(eos)).
      - Used with C(scope=ztp_config).
    type: dict
    required: false
  old_password:
    description:
      - Current ZTP web UI password (required for C(scope=password)).
    type: str
    required: false
    no_log: true
  new_password:
    description:
      - New ZTP web UI password (required for C(scope=password)).
    type: str
    required: false
    no_log: true
"""

EXAMPLES = """
# Query current DHCP configurator state
- name: Get current DHCP configuration
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: query
  register: dhcp_config

- name: Show DHCP config
  ansible.builtin.debug:
    var: dhcp_config.config

# Configure DHCP subnets and host-reservations
- name: Configure DHCP
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: present
    options:
      domain-name: "ztplab.local"
      domain-search: "ztplab.local"
      domain-name-servers:
        - "8.8.8.8"
        - "8.8.4.4"
      tftp-server-name: "192.168.50.2"
    subnets:
      - subnet: "192.168.50.0/24"
        router: "192.168.50.1"
        pools:
          - range-start: "192.168.50.10"
            range-end: "192.168.50.50"
        host-reservations:
          - hw-address: "aa:bb:cc:dd:ee:01"
            ip-address: "192.168.50.100"
            hostname: "switch1"
        reservation-mode:
          - "all"

# Add host-reservations to existing subnet
- name: Add host reservation
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: present
    host_reservations:
      - hw-address: "aa:bb:cc:dd:ee:02"
        ip-address: "192.168.50.101"
        hostname: "switch2"

# Remove a host-reservation
- name: Remove host reservation
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: absent
    host_reservations:
      - hw-address: "aa:bb:cc:dd:ee:02"
        ip-address: "192.168.50.101"

# Query current ZTP JSON config
- name: Get ZTP firmware config
  juniper.apstra.ztp_config:
    scope: ztp_config
    state: query
  register: ztp_fw

- name: Show ZTP config
  ansible.builtin.debug:
    var: ztp_fw.config

# Update ZTP firmware and password config
- name: Update ZTP config
  juniper.apstra.ztp_config:
    scope: ztp_config
    state: present
    firmware:
      defaults:
        device-root-password: "{{ default_root_password }}"
        device-user: "{{ device_user }}"
        device-user-password: "{{ device_user_password }}"
        junos-versions:
          - "25.4R1.12"
      junos:
        device-root-password: "{{ junos_root_password }}"
        device-user-password: "{{ junos_user_password }}"
        system-agent-params:
          agent_type: "offbox"
          job_on_create: "install"
          platform: "junos"

# Change ZTP web UI password
- name: Change ZTP admin password
  juniper.apstra.ztp_config:
    scope: password
    old_password: "{{ current_ztp_password }}"
    new_password: "{{ new_ztp_password }}"
"""

RETURN = """
changed:
  description: Whether any changes were made.
  type: bool
  returned: always
config:
  description: The current or resulting configuration.
  type: dict
  returned: when scope is dhcp_configurator or ztp_config
changes:
  description: Summary of changes applied.
  type: dict
  returned: when changes were made
msg:
  description: Human-readable message describing the outcome.
  type: str
  returned: always
"""

import copy
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ztp_client import (
    ztp_client_module_args,
    ZtpClient,
    ZtpClientError,
)


def _deep_diff(current, desired):
    """
    Recursively compare two dicts/lists and return a dict of changes.
    Returns an empty dict if they are equal.
    """
    if isinstance(current, dict) and isinstance(desired, dict):
        changes = {}
        for key in desired:
            if key not in current:
                changes[key] = {"added": desired[key]}
            elif current[key] != desired[key]:
                sub_diff = _deep_diff(current[key], desired[key])
                if sub_diff:
                    changes[key] = sub_diff
        return changes
    elif isinstance(current, list) and isinstance(desired, list):
        if current != desired:
            return {"before": current, "after": desired}
        return {}
    else:
        if current != desired:
            return {"before": current, "after": desired}
        return {}


def _merge_host_reservations(existing_reservations, new_reservations):
    """
    Merge new host reservations into existing ones.
    Uses hw-address as the unique key. Existing entries with the same
    hw-address are updated; new entries are appended.
    """
    reservation_map = {}
    for res in existing_reservations:
        key = res.get("hw-address", "").lower()
        reservation_map[key] = res

    for res in new_reservations:
        key = res.get("hw-address", "").lower()
        reservation_map[key] = res

    return list(reservation_map.values())


def _remove_host_reservations(existing_reservations, reservations_to_remove):
    """
    Remove host reservations by hw-address from the existing list.
    """
    remove_macs = {r.get("hw-address", "").lower() for r in reservations_to_remove}
    return [
        r
        for r in existing_reservations
        if r.get("hw-address", "").lower() not in remove_macs
    ]


def _handle_dhcp_configurator_query(client, result):
    """Handle scope=dhcp_configurator, state=query."""
    config = client.get_dhcp_configurator()
    result["config"] = config
    result["msg"] = "DHCP configurator configuration retrieved successfully"


def _handle_dhcp_configurator_present(module, client, result):
    """Handle scope=dhcp_configurator, state=present."""
    current_config = client.get_dhcp_configurator()
    desired_config = copy.deepcopy(current_config)

    # Apply options if provided
    options = module.params.get("options")
    if options:
        if "options" not in desired_config:
            desired_config["options"] = {}
        desired_config["options"].update(options)

    # Apply reservation_mode_default if provided
    reservation_mode_default = module.params.get("reservation_mode_default")
    if reservation_mode_default is not None:
        desired_config["reservation-mode-default"] = reservation_mode_default

    # Apply subnets if provided
    subnets = module.params.get("subnets")
    if subnets is not None:
        desired_config["subnets"] = subnets

    # Apply global host reservations if provided
    global_host_reservations = module.params.get("global_host_reservations")
    if global_host_reservations is not None:
        existing_global = desired_config.get("global-host-reservations", [])
        desired_config["global-host-reservations"] = _merge_host_reservations(
            existing_global, global_host_reservations
        )

    # Apply host_reservations — merge into existing subnet(s)
    host_reservations = module.params.get("host_reservations")
    if host_reservations is not None and subnets is None:
        # When no subnets are explicitly provided, merge reservations
        # into the first existing subnet
        existing_subnets = desired_config.get("subnets", [])
        if existing_subnets:
            existing_res = existing_subnets[0].get("host-reservations", [])
            existing_subnets[0]["host-reservations"] = _merge_host_reservations(
                existing_res, host_reservations
            )

    # Compare and apply
    changes = _deep_diff(current_config, desired_config)
    if changes:
        client.update_dhcp_configurator(desired_config)
        result["changed"] = True
        result["changes"] = changes
        result["msg"] = "DHCP configurator configuration updated successfully"
    else:
        result["msg"] = "DHCP configurator configuration is already up to date"

    result["config"] = desired_config


def _handle_dhcp_configurator_absent(module, client, result):
    """Handle scope=dhcp_configurator, state=absent."""
    current_config = client.get_dhcp_configurator()
    desired_config = copy.deepcopy(current_config)

    host_reservations = module.params.get("host_reservations")
    global_host_reservations = module.params.get("global_host_reservations")
    subnets_to_remove = module.params.get("subnets")

    changed = False

    # Remove host reservations from subnets
    if host_reservations:
        existing_subnets = desired_config.get("subnets", [])
        for subnet in existing_subnets:
            existing_res = subnet.get("host-reservations", [])
            new_res = _remove_host_reservations(existing_res, host_reservations)
            if len(new_res) != len(existing_res):
                subnet["host-reservations"] = new_res
                changed = True

    # Remove global host reservations
    if global_host_reservations:
        existing_global = desired_config.get("global-host-reservations", [])
        new_global = _remove_host_reservations(
            existing_global, global_host_reservations
        )
        if len(new_global) != len(existing_global):
            desired_config["global-host-reservations"] = new_global
            changed = True

    # Remove entire subnets by CIDR
    if subnets_to_remove:
        remove_cidrs = {s.get("subnet") for s in subnets_to_remove if s.get("subnet")}
        existing_subnets = desired_config.get("subnets", [])
        new_subnets = [
            s for s in existing_subnets if s.get("subnet") not in remove_cidrs
        ]
        if len(new_subnets) != len(existing_subnets):
            desired_config["subnets"] = new_subnets
            changed = True

    if changed:
        client.update_dhcp_configurator(desired_config)
        result["changed"] = True
        result["changes"] = _deep_diff(current_config, desired_config)
        result["msg"] = "DHCP configurator items removed successfully"
    else:
        result["msg"] = "No matching items found to remove"

    result["config"] = desired_config


def _handle_ztp_config_query(client, result):
    """Handle scope=ztp_config, state=query."""
    config = client.get_ztp_config()
    result["config"] = config.get("data", config)
    result["msg"] = "ZTP configuration retrieved successfully"


def _handle_ztp_config_present(module, client, result):
    """Handle scope=ztp_config, state=present."""
    firmware = module.params.get("firmware")
    if not firmware:
        raise ValueError(
            "'firmware' parameter is required for scope=ztp_config with state=present"
        )

    current_response = client.get_ztp_config()
    current_config = current_response.get("data", current_response)

    # Deep merge: update existing config with provided firmware values
    desired_config = copy.deepcopy(current_config)
    for platform, settings in firmware.items():
        if platform in desired_config:
            if isinstance(desired_config[platform], dict) and isinstance(
                settings, dict
            ):
                desired_config[platform].update(settings)
            else:
                desired_config[platform] = settings
        else:
            desired_config[platform] = settings

    changes = _deep_diff(current_config, desired_config)
    if changes:
        client.update_ztp_config(desired_config)
        result["changed"] = True
        result["changes"] = changes
        result["msg"] = "ZTP configuration updated successfully"
    else:
        result["msg"] = "ZTP configuration is already up to date"

    result["config"] = desired_config


def _handle_password(module, client, result):
    """Handle scope=password."""
    old_password = module.params.get("old_password")
    new_password = module.params.get("new_password")

    if not old_password or not new_password:
        raise ValueError(
            "Both 'old_password' and 'new_password' are required for scope=password"
        )

    if old_password == new_password:
        result["msg"] = "Old and new passwords are the same, no change needed"
        return

    client.change_password(old_password, new_password)
    result["changed"] = True
    result["msg"] = "ZTP admin password changed successfully"


def main():
    ztp_module_args = ztp_client_module_args()
    object_module_args = dict(
        scope=dict(
            type="str",
            required=True,
            choices=["dhcp_configurator", "ztp_config", "password"],
        ),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent", "query"],
            default="present",
        ),
        subnets=dict(type="list", elements="dict", required=False, default=None),
        host_reservations=dict(
            type="list", elements="dict", required=False, default=None
        ),
        global_host_reservations=dict(
            type="list", elements="dict", required=False, default=None
        ),
        options=dict(type="dict", required=False, default=None),
        reservation_mode_default=dict(
            type="list", elements="str", required=False, default=None
        ),
        firmware=dict(type="dict", required=False, default=None),
        old_password=dict(type="str", required=False, no_log=True, default=None),
        new_password=dict(type="str", required=False, no_log=True, default=None),
    )
    module_args = ztp_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client = ZtpClient.from_module_params(module)

        scope = module.params["scope"]
        state = module.params["state"]

        if scope == "dhcp_configurator":
            if state == "query":
                _handle_dhcp_configurator_query(client, result)
            elif state == "present":
                _handle_dhcp_configurator_present(module, client, result)
            elif state == "absent":
                _handle_dhcp_configurator_absent(module, client, result)

        elif scope == "ztp_config":
            if state == "query":
                _handle_ztp_config_query(client, result)
            elif state == "present":
                _handle_ztp_config_present(module, client, result)
            elif state == "absent":
                raise ValueError(
                    "state=absent is not supported for scope=ztp_config. "
                    "Use state=present with the desired configuration."
                )

        elif scope == "password":
            if state != "present":
                raise ValueError("Only state=present is supported for scope=password.")
            _handle_password(module, client, result)

    except (ZtpClientError, ValueError) as e:
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)
    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
