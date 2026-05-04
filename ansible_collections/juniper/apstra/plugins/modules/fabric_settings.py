#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: fabric_settings

short_description: Manage fabric settings in an Apstra blueprint

version_added: "0.2.0"

author:
  - "Vamsi Gavini (@vgavini)"

description:
  - This module manages fabric-wide settings within an Apstra
    blueprint.
  - Settings include MTU values, EVPN parameters, overlay protocol,
    anti-affinity policies, default SVI/anycast configuration, and
    more.
  - Uses the Apstra fabric-settings API via the AOS SDK.
  - Provides full idempotency. Current settings are fetched and
    compared before updating.
  - Only the settings specified in C(settings) are modified; other
    fabric settings remain unchanged.

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
      - The Apstra username for authentication.
    type: str
    required: false
  password:
    description:
      - The Apstra password for authentication.
    type: str
    required: false
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  id:
    description:
      - Identifies the blueprint scope.
      - Must contain C(blueprint) key with the blueprint ID.
    type: dict
    required: true
    suboptions:
      blueprint:
        description:
          - The ID of the blueprint in which to manage fabric settings.
        type: str
        required: true
  body:
    description:
      - A dictionary of fabric settings to apply.
      - Only the keys provided will be updated; unspecified keys remain
        unchanged.
      - Common keys include C(external_router_mtu), C(fabric_l3_mtu),
        C(spine_leaf_links_mtu), C(esi_mac_msb), C(anti_affinity),
        C(junos_evpn_max_nexthop_count),
        C(junos_evpn_routing_instance_mode_allowed),
        C(max_evpn_routes), C(overlay_control_protocol),
        C(default_svi_l3_mtu), C(default_anycast_gw_mac), etc.
    type: dict
    required: true
"""

EXAMPLES = """
# ── Set fabric MTU ────────────────────────────────────────────────

- name: Configure fabric L3 MTU
  juniper.apstra.fabric_settings:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      fabric_l3_mtu: 9170
      spine_leaf_links_mtu: 9170
      external_router_mtu: 9100

# ── Configure EVPN settings ──────────────────────────────────────

- name: Set EVPN overlay parameters
  juniper.apstra.fabric_settings:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      overlay_control_protocol: "evpn"
      max_evpn_routes: 10000
      junos_evpn_max_nexthop_count: 2

# ── Set anycast gateway MAC ───────────────────────────────────────

- name: Configure default anycast GW MAC
  juniper.apstra.fabric_settings:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      default_anycast_gw_mac: "00:00:5e:00:01:01"

# ── Set anti-affinity policy ─────────────────────────────────────

- name: Configure anti-affinity settings
  juniper.apstra.fabric_settings:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      anti_affinity:
        algorithm: "heuristic_enabled"
        max_links_count_per_slot: 1
        max_links_per_slot: 1
        max_svi_inter_count: 0

# ── ESI MAC configuration ────────────────────────────────────────

- name: Set ESI MAC MSB
  juniper.apstra.fabric_settings:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      esi_mac_msb: 2

# ── Full fabric settings for a new blueprint ─────────────────────

- name: Apply full fabric settings
  juniper.apstra.fabric_settings:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      fabric_l3_mtu: 9170
      spine_leaf_links_mtu: 9170
      external_router_mtu: 9100
      overlay_control_protocol: "evpn"
      default_anycast_gw_mac: "00:00:5e:00:01:01"
      esi_mac_msb: 2
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
settings:
  description: The complete fabric settings after the operation.
  type: dict
  returned: always
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


# ──────────────────────────────────────────────────────────────────
#  SDK helpers
# ──────────────────────────────────────────────────────────────────


def _get_l3clos_client(client_factory):
    """Return the l3clos client."""
    return client_factory.get_l3clos_client()


def _get_settings(client_factory, blueprint_id):
    """GET /api/blueprints/{id}/fabric-settings."""
    client = _get_l3clos_client(client_factory)
    return client.blueprints[blueprint_id].fabric_settings.get()


def _update_settings(client_factory, blueprint_id, data):
    """PATCH /api/blueprints/{id}/fabric-settings."""
    client = _get_l3clos_client(client_factory)
    return client.blueprints[blueprint_id].fabric_settings.update(data)


def _deep_compare(current, desired):
    """Compare current settings against desired, return changed keys.

    Only check keys present in desired. Supports nested dicts.

    Returns:
        tuple: (diff_dict, has_changes) — the dict of changes and
        whether there are any differences.
    """
    diff = {}
    has_changes = False

    for key, desired_value in desired.items():
        current_value = current.get(key)

        if isinstance(desired_value, dict) and isinstance(current_value, dict):
            nested_diff, nested_changed = _deep_compare(current_value, desired_value)
            if nested_changed:
                diff[key] = desired_value  # Send the full desired for the key
                has_changes = True
        elif current_value != desired_value:
            diff[key] = desired_value
            has_changes = True

    return diff, has_changes


# ──────────────────────────────────────────────────────────────────
#  Main logic
# ──────────────────────────────────────────────────────────────────


def _handle_settings(module, client_factory):
    """Apply fabric settings — always state=present for settings."""
    p = module.params
    id_param = p["id"] or {}
    blueprint_id = id_param.get("blueprint")
    if blueprint_id:
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
        id_param["blueprint"] = blueprint_id
    desired_settings = p["body"]

    if not desired_settings:
        raise ValueError("'settings' must contain at least one key to update")

    # Fetch current settings
    current = _get_settings(client_factory, blueprint_id)
    if current is None:
        current = {}

    # Compare
    diff, has_changes = _deep_compare(current, desired_settings)

    if not has_changes:
        return dict(
            changed=False,
            settings=current,
            msg="fabric settings already up to date",
        )

    # Apply only the changed fields
    _update_settings(client_factory, blueprint_id, desired_settings)

    # Build final state by merging desired into current (avoids stale cache)
    final = dict(current)
    for k, v in desired_settings.items():
        if isinstance(v, dict) and isinstance(final.get(k), dict):
            final[k] = dict(final[k], **v)
        else:
            final[k] = v
    changed_keys = list(diff.keys())
    return dict(
        changed=True,
        settings=final,
        msg=f"fabric settings updated: {', '.join(changed_keys)}",
    )


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=True),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)
        result = _handle_settings(module, client_factory)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
