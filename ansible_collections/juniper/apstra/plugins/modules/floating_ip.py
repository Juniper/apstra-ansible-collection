#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: floating_ip
short_description: Manage Floating IPs in an Apstra blueprint
description:
  - Create, update, query, or delete Floating IP addresses within an Apstra blueprint.
  - Floating IPs (VIP endpoints) are typically auto-created by Apstra when
    Connectivity Templates assign them.  This module also allows creating them
    manually, renaming them (C(label)), setting a C(description), and changing
    the IP address (C(ipv4_addr) / C(ipv6_addr)).
  - Use C(state=queried) to list all floating IPs or retrieve a single one.
  - Use C(state=present) to create or update a floating IP (idempotent).
  - Use C(state=absent) to delete a floating IP.
version_added: "0.1.0"
author:  "Vamsi Gavini (@vgavini)"
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
    default: true
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
      - Identifies the blueprint and optionally the floating IP node.
      - C(blueprint) (str, required) — blueprint name or UUID.
      - C(floating_ip) (str, optional) — floating IP node UUID.
        If omitted, the module searches by C(body.label) or C(body.ipv4_addr).
        For creation, a UUID is auto-generated when no existing floating IP is found.
    type: dict
    required: true
  body:
    description:
      - Desired properties of the floating IP.
      - C(label) (str) — display name shown in the Apstra UI.
      - C(description) (str) — free-text description.
      - C(ipv4_addr) (str) — IPv4 address in CIDR format (e.g. C(10.2.22.201/24)).
      - C(ipv6_addr) (str) — IPv6 address in CIDR format.
      - C(virtual_network) (str) — Virtual network name or UUID. Used as a lookup
        key to find the floating IP that belongs to that VN. Particularly useful for
        auto-created floating IPs which have no label.
      - C(virtual_network_id) (str) — UUID of the associated virtual network (create only).
      - C(vn_endpoints) (list) — list of VN endpoint IDs (create only).
      - C(generic_system_ids) (list) — list of generic system IDs (create only).
      - When C(state=present), only supplied fields are changed.
    type: dict
    required: false
  state:
    description:
      - C(present) — create or update the floating IP (idempotent).
      - C(absent) — delete the floating IP.
      - C(queried) — list all floating IPs or retrieve a single one (read-only).
    type: str
    required: false
    default: present
    choices: ["present", "absent", "queried"]
"""

EXAMPLES = """
# List all floating IPs in a blueprint
- name: List floating IPs
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
    state: queried
  register: fip_result

- name: Show floating IPs
  ansible.builtin.debug:
    var: fip_result.floating_ips

# Get a single floating IP by node ID
- name: Get floating IP by ID
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
      floating_ip: "{{ fip_node_id }}"
    state: queried
  register: fip

# Create a new floating IP (POST)
- name: Create a floating IP
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
    body:
      label: "Tenant5-VIP"
      description: "Primary VIP for Tenant5"
      ipv4_addr: "10.2.22.201/24"
    state: present
  register: fip_create

# --- PATCH (update) examples ---
# The module detects whether the floating IP already exists.
# If it does, it issues a PATCH with only the changed fields.

# PATCH by node ID — most explicit; supply id.floating_ip directly
- name: Update floating IP label by node ID (PATCH)
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
      floating_ip: "{{ fip_node_id }}"
    body:
      label: "Tenant5-VIP-renamed"
      description: "Updated description"
    state: present

# PATCH by label — module looks up the node ID first, then PATCHes
- name: Update floating IP address by label lookup (PATCH)
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
    body:
      label: "Tenant5-VIP"          # used to FIND the floating IP
      ipv4_addr: "10.2.22.210/24"   # new address to set via PATCH
    state: present

# PATCH by VN name — finds the floating IP that belongs to a virtual network.
# Auto-created floating IPs have no label; use virtual_network to locate them.
- name: Name an auto-created floating IP by its VN (PATCH)
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
    body:
      virtual_network: "Tenant2-VLAN22"   # VN name or UUID — used to FIND the floating IP
      label: "Tenant2-VIP"                # new label to set via PATCH
      description: "Auto-created VIP for Tenant2"
    state: present

# PATCH by IPv4 address — useful when label is unknown
- name: Update floating IP description by ipv4_addr lookup (PATCH)
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
    body:
      ipv4_addr: "10.2.22.201/24"   # used to FIND the floating IP
      description: "Found by IP"    # new description to set via PATCH
    state: present

# Idempotent update — no change if values already match
- name: Ensure floating IP has expected label (idempotent PATCH)
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
      floating_ip: "{{ fip_node_id }}"
    body:
      label: "Tenant5-VIP"
    state: present

# Delete a floating IP by label
- name: Delete floating IP
  juniper.apstra.floating_ip:
    id:
      blueprint: "my-blueprint"
    body:
      label: "Tenant5-VIP"
    state: absent
"""

RETURN = """
changed:
    description: Whether the floating IP was changed.
    returned: always
    type: bool
floating_ip:
    description: The current state of the floating IP after the operation.
    returned: when state is present and a single floating IP is targeted
    type: dict
    sample:
        id: "abc123"
        label: "Tenant5-VIP"
        description: "Primary VIP for Tenant5"
        ipv4_addr: "10.2.22.201/24"
        immutable: false
floating_ips:
    description: List of all floating IPs in the blueprint.
    returned: when state is queried and no floating_ip ID is specified
    type: list
    elements: dict
msg:
    description: Human-readable result message.
    returned: always
    type: str
"""

import traceback
import uuid

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    ApstraClientFactory,
    apstra_client_module_args,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_virtual_network_id,
)


def _get_blueprint_client(client_factory, blueprint_id):
    """Return the l3clos blueprint resource handle."""
    l3clos = client_factory.get_l3clos_client()
    return l3clos.blueprints[blueprint_id]


def _list_all(bp):
    """Return all floating IPs with IDs via experience/web endpoint."""
    result = bp.experience.web.floating_ips.get()
    if result is None:
        return []
    if isinstance(result, list):
        return result
    return []


def _find_by_label(all_fips, label):
    """Return the first floating IP dict whose label matches."""
    for fip in all_fips:
        if fip.get("label") == label:
            return fip
    return None


def _find_by_ipv4(all_fips, ipv4_addr):
    """Return the first floating IP dict whose ipv4_addr matches."""
    for fip in all_fips:
        if fip.get("ipv4_addr") == ipv4_addr:
            return fip
    return None


def _find_by_vn_id(all_fips, vn_id):
    """Return the first floating IP dict whose virtual_network_id matches."""
    for fip in all_fips:
        if fip.get("virtual_network_id") == vn_id:
            return fip
    return None


def _needs_update(current, desired):
    """Return dict of fields that differ between current and desired."""
    changes = {}
    for key, value in desired.items():
        if current.get(key) != value:
            changes[key] = value
    return changes


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent", "queried"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        id_param = dict(module.params.get("id") or {})
        body = module.params.get("body") or {}
        state = module.params["state"]

        blueprint_id = id_param.get("blueprint")
        if not blueprint_id:
            raise ValueError("'id.blueprint' is required")
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)

        node_id = id_param.get("floating_ip")

        bp = _get_blueprint_client(client_factory, blueprint_id)

        # ── state=queried ────────────────────────────────────────────────
        if state == "queried":
            if node_id:
                fip = bp.floating_ips[node_id].get()
                if fip is None:
                    raise ValueError(
                        f"Floating IP node '{node_id}' not found in blueprint '{blueprint_id}'"
                    )
                result["floating_ip"] = fip
                result["msg"] = f"floating_ip '{node_id}' retrieved"
            else:
                all_fips = _list_all(bp)
                result["floating_ips"] = all_fips
                result["msg"] = f"found {len(all_fips)} floating IP(s)"
            result["changed"] = False
            module.exit_json(**result)
            return

        # ── Resolve node_id from body if not provided ────────────────────
        current_fip = None
        create_mode = False
        if not node_id:
            all_fips = _list_all(bp)
            label = body.get("label")
            ipv4_addr = body.get("ipv4_addr")
            virtual_network = body.pop("virtual_network", None)

            # Try label first, then ipv4_addr, then virtual_network as lookup keys
            if label:
                current_fip = _find_by_label(all_fips, label)
            if current_fip is None and ipv4_addr:
                current_fip = _find_by_ipv4(all_fips, ipv4_addr)
            if current_fip is None and virtual_network:
                vn_id = resolve_virtual_network_id(
                    client_factory, blueprint_id, virtual_network
                )
                current_fip = _find_by_vn_id(all_fips, vn_id)

            if current_fip is None:
                if state == "absent":
                    # Nothing to delete
                    result["changed"] = False
                    result["msg"] = "floating_ip not found, nothing to delete"
                    module.exit_json(**result)
                    return
                # state=present + not found → create
                create_mode = True
                node_id = str(uuid.uuid4())
            else:
                node_id = current_fip["id"]
        else:
            # Fetch current state by node_id from experience/web (includes id + immutable)
            all_fips = _list_all(bp)
            for fip in all_fips:
                if fip.get("id") == node_id:
                    current_fip = fip
                    break
            if current_fip is None:
                if state == "absent":
                    result["changed"] = False
                    result["msg"] = (
                        f"floating_ip '{node_id}' not found, nothing to delete"
                    )
                    module.exit_json(**result)
                    return
                create_mode = True

        result["id"] = {"blueprint": blueprint_id, "floating_ip": node_id}

        # ── state=absent ─────────────────────────────────────────────────
        if state == "absent":
            bp.floating_ips[node_id].delete()
            result["changed"] = True
            result["msg"] = f"floating_ip '{node_id}' deleted"
            module.exit_json(**result)
            return

        # ── state=present / create ────────────────────────────────────────
        if create_mode:
            create_fields = (
                "label",
                "description",
                "virtual_network_id",
                "vn_endpoints",
                "ipv4_addr",
                "ipv6_addr",
                "generic_system_ids",
            )
            create_payload = {"id": node_id, "immutable": False}
            for field in create_fields:
                if field in body:
                    create_payload[field] = body[field]
            create_result = bp.floating_ips.create(create_payload)
            # Use the ID returned by Apstra (it may differ from the one we proposed)
            node_id = (create_result or {}).get("id") or node_id
            result["id"] = {"blueprint": blueprint_id, "floating_ip": node_id}
            # Fetch the created floating IP
            created = bp.floating_ips[node_id].get() or {}
            created["id"] = node_id
            result["changed"] = True
            result["floating_ip"] = created
            result["msg"] = f"floating_ip '{node_id}' created"
            module.exit_json(**result)
            return

        # ── state=present / update ────────────────────────────────────────
        patchable = {}
        for field in ("label", "description", "ipv4_addr", "ipv6_addr"):
            if field in body:
                patchable[field] = body[field]

        if not patchable:
            result["changed"] = False
            result["floating_ip"] = current_fip
            result["msg"] = "no fields to update"
            module.exit_json(**result)
            return

        changes = _needs_update(current_fip, patchable)
        if not changes:
            result["changed"] = False
            result["floating_ip"] = current_fip
            result["msg"] = "floating_ip already up to date, no change"
            module.exit_json(**result)
            return

        # Use the graph-nodes endpoint to patch — the facade endpoint
        # rejects patches on FIPs it considers immutable, but graph-node
        # update works for all patchable fields (label, description, etc.).
        l3clos = client_factory.get_l3clos_client()
        l3clos.blueprints[blueprint_id].nodes[node_id].update(
            changes, allow_unsafe=True
        )
        result["changed"] = True
        result["changes"] = changes

        # Merge changes into current state — re-fetching via experience/web
        # returns stale data immediately after a graph-node update.
        updated = {**(current_fip or {}), **changes}
        result["floating_ip"] = updated
        result["msg"] = f"floating_ip '{node_id}' updated: {', '.join(changes.keys())}"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
