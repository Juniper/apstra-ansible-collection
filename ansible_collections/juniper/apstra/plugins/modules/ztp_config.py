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

version_added: "1.1.0"

author:
  - "Prabhanjan KV (@kvp-hpe)"

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
    default: true
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
      - Optional C(subnet) to target a specific existing subnet instead of
        using the first configured subnet.
      - Optional C(pool-range-start) and C(pool-range-end) to target a
        specific pool within the selected subnet. These selector keys are
        used only by the module and are not sent to the ZTP API.
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
# =============================================================================
# DHCP CONFIGURATOR SCOPE — Query, Update, Reservations
# =============================================================================

# Query current DHCP configurator state
- name: Get current DHCP configuration
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: query
  register: dhcp_config

- name: Show DHCP config
  ansible.builtin.debug:
    var: dhcp_config.config

# Configure DHCP subnets, pools, options, and host-reservations
# This example shows all available DHCP options
- name: Configure DHCP with all options
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
          - hw-address: "aa:bb:cc:dd:ee:02"
            ip-address: "192.168.50.101"
            hostname: "switch2"
        reservation-mode:
          - "all"

# Configure multiple DHCP subnets with separate pools
- name: Configure multiple subnets
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: present
    subnets:
      - subnet: "192.168.50.0/24"
        router: "192.168.50.1"
        pools:
          - range-start: "192.168.50.10"
            range-end: "192.168.50.50"
      - subnet: "10.0.0.0/24"
        router: "10.0.0.1"
        pools:
          - range-start: "10.0.0.10"
            range-end: "10.0.0.100"

# Add a host-reservation to a specific pool in an existing subnet
- name: Add host reservation to a selected pool
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: present
    host_reservations:
      - subnet: "192.168.50.0/24"
        pool-range-start: "192.168.50.60"
        pool-range-end: "192.168.50.80"
        hw-address: "aa:bb:cc:dd:ee:03"
        ip-address: "192.168.50.65"
        hostname: "switch3"

# Add a host-reservation to a specific subnet without replacing others
- name: Add host reservation to a selected subnet
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: present
    host_reservations:
      - subnet: "10.0.0.0/24"
      - hw-address: "aa:bb:cc:dd:ee:03"
        ip-address: "10.0.0.25"
        hostname: "switch3-alt"

# Add global host reservations (outside any subnet)
- name: Add global host reservation
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: present
    global_host_reservations:
      - hw-address: "aa:bb:cc:dd:ee:ff"
        ip-address: "10.10.10.100"
        hostname: "global-device"

# Set default reservation mode
- name: Set reservation mode
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: present
    reservation_mode_default:
      - "all"

# Remove a host-reservation by MAC address
- name: Remove host reservation
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: absent
    host_reservations:
      - hw-address: "aa:bb:cc:dd:ee:03"
        ip-address: "192.168.50.102"

# Remove an entire subnet
- name: Remove a subnet
  juniper.apstra.ztp_config:
    scope: dhcp_configurator
    state: absent
    subnets:
      - subnet: "10.0.0.0/24"

# =============================================================================
# ZTP CONFIG SCOPE — Query, Update firmware/password/agent settings
# =============================================================================

# Query current ZTP JSON config
- name: Get ZTP firmware config
  juniper.apstra.ztp_config:
    scope: ztp_config
    state: query
  register: ztp_fw

- name: Show ZTP config
  ansible.builtin.debug:
    var: ztp_fw.config

# Configure complete ZTP JSON with all platform blocks
# This manages the full ztp.json used by the ZTP VM for device provisioning
- name: Configure complete ZTP JSON
  juniper.apstra.ztp_config:
    scope: ztp_config
    state: present
    firmware:
      defaults:
        device-root-password: "admin"
        device-user: "aosadmin"
        device-user-password: "aosadmin"
        dual-routing-engine: false
        junos-versions:
          - "25.4R1.12"
        junos-evo-image: "http://server/path/to/junos-evo-install.tgz"
        junos-evo-versions:
          - "junos-evo-version1"
        eos-image: "aos_eos_image.bin"
        eos-versions:
          - "eos-version1"
          - "eos-version2"
        nxos-image: "aos_nxos_image.bin"
        nxos-versions:
          - "nxos-version1"
        sonic-image: "http://server/path/to/sonic.bin"
        sonic-versions:
          - "sonic-version1"
          - "sonic-version2"
        management-subnet-prefixlen: 0
        system-agent-params:
          agent_type: "onbox"
      junos:
        device-root-password: "Juniper123"
        device-user-password: "Juniper123"
        system-agent-params:
          agent_type: "offbox"
          job_on_create: "install"
          platform: "junos"
      junos-evo:
        device-root-password: "root123"
        device-user-password: "aosadmin123"
        system-agent-params:
          agent_type: "offbox"
          job_on_create: "install"
          platform: "junos"
      eos:
        custom-config: "eos_custom.sh"
      nxos:
        device-root-password: "admin123"
        system-agent-params:
          agent_type: "onbox"

# Update only Junos settings (other platforms are preserved)
# The module does a deep merge — only specified keys are updated
- name: Update Junos ZTP settings only
  juniper.apstra.ztp_config:
    scope: ztp_config
    state: present
    firmware:
      junos:
        device-root-password: "{{ junos_root_password }}"
        device-user-password: "{{ junos_user_password }}"
        system-agent-params:
          agent_type: "offbox"
          job_on_create: "install"
          platform: "junos"

# Update default settings only
- name: Update default ZTP settings
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

# =============================================================================
# PASSWORD SCOPE — Change ZTP web UI admin password
# =============================================================================

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
import ipaddress
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


def _pool_key(pool):
    """Return a stable key for a DHCP pool range."""
    return (pool.get("range-start"), pool.get("range-end"))


def _merge_pools(existing_pools, new_pools):
    """Merge pools by range so new pools append without replacing others."""
    pool_map = {_pool_key(pool): copy.deepcopy(pool) for pool in existing_pools}
    ordered_keys = [_pool_key(pool) for pool in existing_pools]

    for pool in new_pools:
        key = _pool_key(pool)
        if key not in pool_map:
            ordered_keys.append(key)
        pool_map[key] = copy.deepcopy(pool)

    return [pool_map[key] for key in ordered_keys]


def _merge_subnets(existing_subnets, new_subnets):
    """Merge subnets by CIDR so adding one subnet preserves unrelated entries."""
    merged_subnets = [copy.deepcopy(subnet) for subnet in existing_subnets]
    subnet_index = {
        subnet.get("subnet"): index
        for index, subnet in enumerate(merged_subnets)
        if subnet.get("subnet")
    }

    for subnet in new_subnets:
        subnet_cidr = subnet.get("subnet")
        if subnet_cidr and subnet_cidr in subnet_index:
            current_subnet = merged_subnets[subnet_index[subnet_cidr]]
            updated_subnet = copy.deepcopy(current_subnet)

            for key, value in subnet.items():
                if key == "pools" and value is not None:
                    updated_subnet["pools"] = _merge_pools(
                        current_subnet.get("pools", []), value
                    )
                elif key == "host-reservations" and value is not None:
                    updated_subnet["host-reservations"] = _merge_host_reservations(
                        current_subnet.get("host-reservations", []), value
                    )
                else:
                    updated_subnet[key] = copy.deepcopy(value)

            merged_subnets[subnet_index[subnet_cidr]] = updated_subnet
        else:
            merged_subnets.append(copy.deepcopy(subnet))
            if subnet_cidr:
                subnet_index[subnet_cidr] = len(merged_subnets) - 1

    return merged_subnets


def _reservation_payload(reservation):
    """Strip module-only subnet/pool selectors from reservation payloads."""
    payload = copy.deepcopy(reservation)
    payload.pop("subnet", None)
    payload.pop("pool-range-start", None)
    payload.pop("pool-range-end", None)
    return payload


def _find_subnet_by_pool(subnets, pool_start, pool_end):
    """Find a subnet index by exact pool range."""
    matches = []
    for index, subnet in enumerate(subnets):
        for pool in subnet.get("pools", []):
            if _pool_key(pool) == (pool_start, pool_end):
                matches.append(index)
                break
    return matches


def _validate_reservation_pool(reservation, pool_start, pool_end):
    """Ensure the reservation IP is inside the selected pool range."""
    ip_address = reservation.get("ip-address")
    if not ip_address:
        return

    reservation_ip = ipaddress.ip_address(ip_address)
    start_ip = ipaddress.ip_address(pool_start)
    end_ip = ipaddress.ip_address(pool_end)
    if not start_ip <= reservation_ip <= end_ip:
        raise ValueError(
            "Reservation IP '{0}' is outside the selected pool range "
            "'{1}'-'{2}'".format(ip_address, pool_start, pool_end)
        )


def _select_subnet_for_reservation(subnets, reservation):
    """Resolve which subnet receives a host reservation."""
    subnet_cidr = reservation.get("subnet")
    pool_start = reservation.get("pool-range-start")
    pool_end = reservation.get("pool-range-end")

    if bool(pool_start) != bool(pool_end):
        raise ValueError(
            "Both 'pool-range-start' and 'pool-range-end' are required when "
            "targeting a specific pool"
        )

    if subnet_cidr:
        for index, subnet in enumerate(subnets):
            if subnet.get("subnet") == subnet_cidr:
                if pool_start and pool_end:
                    pools = subnet.get("pools", [])
                    if _pool_key(
                        {"range-start": pool_start, "range-end": pool_end}
                    ) not in {_pool_key(pool) for pool in pools}:
                        raise ValueError(
                            "Pool '{0}'-'{1}' was not found in subnet '{2}'".format(
                                pool_start, pool_end, subnet_cidr
                            )
                        )
                    _validate_reservation_pool(reservation, pool_start, pool_end)
                return index
        raise ValueError("Subnet '{0}' was not found".format(subnet_cidr))

    if pool_start and pool_end:
        matches = _find_subnet_by_pool(subnets, pool_start, pool_end)
        if not matches:
            raise ValueError(
                "Pool '{0}'-'{1}' was not found in the current DHCP configuration".format(
                    pool_start, pool_end
                )
            )
        if len(matches) > 1:
            raise ValueError(
                "Pool '{0}'-'{1}' exists in multiple subnets; specify 'subnet' "
                "to disambiguate the target".format(pool_start, pool_end)
            )
        _validate_reservation_pool(reservation, pool_start, pool_end)
        return matches[0]

    if subnets:
        return 0

    raise ValueError(
        "No subnets are configured. Provide 'subnets' first or include a new subnet "
        "definition in the same task."
    )


def _merge_targeted_host_reservations(desired_config, host_reservations):
    """Merge host reservations into the requested subnet without replacing others."""
    existing_subnets = desired_config.get("subnets", [])
    if not existing_subnets:
        raise ValueError(
            "No DHCP subnets are configured. Configure at least one subnet before "
            "adding host reservations."
        )

    reservations_by_subnet = {}
    for reservation in host_reservations:
        subnet_index = _select_subnet_for_reservation(existing_subnets, reservation)
        reservations_by_subnet.setdefault(subnet_index, []).append(
            _reservation_payload(reservation)
        )

    for subnet_index, reservations in reservations_by_subnet.items():
        existing_reservations = existing_subnets[subnet_index].get(
            "host-reservations", []
        )
        existing_subnets[subnet_index]["host-reservations"] = _merge_host_reservations(
            existing_reservations, reservations
        )


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
        desired_config["subnets"] = _merge_subnets(
            desired_config.get("subnets", []), subnets
        )

    # Apply global host reservations if provided
    global_host_reservations = module.params.get("global_host_reservations")
    if global_host_reservations is not None:
        existing_global = desired_config.get("global-host-reservations", [])
        desired_config["global-host-reservations"] = _merge_host_reservations(
            existing_global, global_host_reservations
        )

    # Apply host_reservations — merge into the selected subnet or pool
    host_reservations = module.params.get("host_reservations")
    if host_reservations is not None:
        _merge_targeted_host_reservations(desired_config, host_reservations)

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
