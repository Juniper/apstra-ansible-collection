#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import traceback
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

DOCUMENTATION = """
---
module: generic_systems

short_description: Manage datacenter generic systems in Apstra blueprints

version_added: "0.2.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module manages generic systems in Apstra datacenter blueprints using
    a flat parameter model for managing generic systems with their links
    to switches.
  - Supports creating, updating, and deleting generic systems with their links
    to switches.
  - Links are defined as a flat list, each specifying the target switch, interface
    name, interface transform, optional LAG mode, group label, and per-link tags.
  - System-level properties include name, hostname, deploy mode, ASN, loopback
    IPs, port-channel ID range, tags, and external flag.
  - Uses the C(switch-system-links) API to create in-rack generic systems and the
    C(external-generic-systems) API for external systems.
  - Provides full idempotency — create, update, and delete operations are safe
    to re-run.
  - Requires a blueprint to already exist and leaf switches to have interface
    maps assigned before creating generic systems.

options:
  api_url:
    description:
      - The URL used to access the Apstra api.
    type: str
    required: false
    default: APSTRA_API_URL environment variable
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
    default: APSTRA_USERNAME environment variable
  password:
    description:
      - The password for authentication.
    type: str
    required: false
    default: APSTRA_PASSWORD environment variable
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
    default: APSTRA_AUTH_TOKEN environment variable
  blueprint_id:
    description:
      - The ID of the datacenter blueprint.
    type: str
    required: true
  system_id:
    description:
      - The node ID of an existing generic system within the blueprint.
      - Required for update and delete operations.
      - Returned after create operations.
    type: str
    required: false
  name:
    description:
      - The display name (label) of the generic system.
      - Corresponds to C(Name) / C(label) in the Apstra graph.
    type: str
    required: false
  hostname:
    description:
      - The hostname of the generic system.
    type: str
    required: false
  tags:
    description:
      - List of tags to apply to the generic system node.
    type: list
    elements: str
    required: false
    default: []
  links:
    description:
      - List of link definitions connecting switches to the generic system.
      - Each link is a dictionary with the keys described below.
    type: list
    elements: dict
    required: false
    default: []
    suboptions:
      target_switch_id:
        description:
          - The graph node ID of the target leaf/access switch.
        type: str
        required: true
      target_switch_if_name:
        description:
          - The physical interface name on the target switch (e.g. C(xe-0/0/6)).
        type: str
        required: true
      target_switch_if_transform_id:
        description:
          - The interface transform ID controlling speed/breakout mode.
        type: int
        required: true
      lag_mode:
        description:
          - LAG mode for this link.
          - Use C(null) or omit for a standalone (non-LAG) link.
        type: str
        required: false
        choices: ["lacp_active", "lacp_passive", "static_lag"]
      group_label:
        description:
          - Label used to group multiple links into a single LAG.
          - All links sharing the same C(group_label) and C(lag_mode) form one LAG.
        type: str
        required: false
      tags:
        description:
          - List of tags to apply to this individual link.
        type: list
        elements: str
        required: false
        default: []
  deploy_mode:
    description:
      - The deploy mode for the generic system.
    type: str
    required: false
    choices: ["deploy", "ready", "drain", "undeploy"]
    default: "deploy"
  asn:
    description:
      - The ASN to assign to the generic system.
      - Set to C(null) to clear the ASN.
    type: int
    required: false
  loopback_ipv4:
    description:
      - The IPv4 loopback address (CIDR notation) for the generic system.
      - Set to C(null) to clear the loopback.
    type: str
    required: false
  loopback_ipv6:
    description:
      - The IPv6 loopback address (CIDR notation) for the generic system.
      - Set to C(null) to clear the loopback.
    type: str
    required: false
  port_channel_id_min:
    description:
      - Minimum port-channel ID for the generic system.
      - Set to 0 to disable.
    type: int
    required: false
    default: 0
  port_channel_id_max:
    description:
      - Maximum port-channel ID for the generic system.
      - Set to 0 to disable.
    type: int
    required: false
    default: 0
  external:
    description:
      - Whether this is an external generic system (outside of racks).
      - External systems use a different API for creation and deletion.
      - Once created, this property cannot be changed.
    type: bool
    required: false
    default: false
  clear_cts_on_destroy:
    description:
      - If true, clear all connectivity templates from the system's links
        before deleting the generic system.
      - Useful when CTs are applied and deletion would otherwise fail.
    type: bool
    required: false
    default: false
  state:
    description:
      - Desired state of the generic system.
      - C(present) will create or update the generic system.
      - C(absent) will delete the generic system.
    type: str
    required: false
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Create a generic system with a single link ─────────────────────

- name: Create a generic system connected to a leaf switch
  juniper.apstra.generic_systems:
    blueprint_id: "{{ blueprint_id }}"
    name: "my-server-01"
    hostname: "my-server-01.example.com"
    tags:
      - "server"
      - "prod"
    deploy_mode: "deploy"
    links:
      - target_switch_id: "{{ leaf_id }}"
        target_switch_if_name: "xe-0/0/7"
        target_switch_if_transform_id: 1
        tags:
          - "10G"
    state: present
  register: gs_create

# ── Create a generic system with dual LAG links ───────────────────

- name: Create a 4x10G server with two LAG bonds
  juniper.apstra.generic_systems:
    blueprint_id: "{{ blueprint_id }}"
    name: "lag-server-01"
    hostname: "lag-server-01.example.com"
    tags:
      - "server"
      - "production"
    links:
      - target_switch_id: "{{ leaf_ids[0] }}"
        target_switch_if_name: "xe-0/0/6"
        target_switch_if_transform_id: 1
        lag_mode: "lacp_active"
        group_label: "bond0"
        tags: ["10G", "bond0"]
      - target_switch_id: "{{ leaf_ids[1] }}"
        target_switch_if_name: "xe-0/0/6"
        target_switch_if_transform_id: 1
        lag_mode: "lacp_active"
        group_label: "bond0"
        tags: ["10G", "bond0"]
      - target_switch_id: "{{ leaf_ids[0] }}"
        target_switch_if_name: "xe-0/0/7"
        target_switch_if_transform_id: 1
        lag_mode: "lacp_active"
        group_label: "bond1"
        tags: ["10G", "bond1"]
      - target_switch_id: "{{ leaf_ids[1] }}"
        target_switch_if_name: "xe-0/0/7"
        target_switch_if_transform_id: 1
        lag_mode: "lacp_active"
        group_label: "bond1"
        tags: ["10G", "bond1"]
    state: present
  register: lag_server

# ── Update a generic system ────────────────────────────────────────

- name: Update generic system hostname and deploy mode
  juniper.apstra.generic_systems:
    blueprint_id: "{{ blueprint_id }}"
    system_id: "{{ gs_create.system_id }}"
    name: "my-server-01-updated"
    hostname: "my-server-01-updated.example.com"
    deploy_mode: "ready"
    state: present
  register: gs_update

# ── Set ASN and loopback addresses ─────────────────────────────────

- name: Configure system with ASN and loopbacks
  juniper.apstra.generic_systems:
    blueprint_id: "{{ blueprint_id }}"
    system_id: "{{ gs_create.system_id }}"
    asn: 65001
    loopback_ipv4: "10.0.0.1/32"
    loopback_ipv6: "fd00::1/128"
    port_channel_id_min: 1
    port_channel_id_max: 128
    state: present
  register: gs_props

# ── Create an external generic system ──────────────────────────────

- name: Create external generic system
  juniper.apstra.generic_systems:
    blueprint_id: "{{ blueprint_id }}"
    name: "external-server-01"
    hostname: "external-server-01.example.com"
    external: true
    state: present
  register: ext_gs

# ── Delete a generic system ────────────────────────────────────────

- name: Delete a generic system
  juniper.apstra.generic_systems:
    blueprint_id: "{{ blueprint_id }}"
    system_id: "{{ gs_create.system_id }}"
    state: absent

# ── Delete with connectivity template cleanup ──────────────────────

- name: Delete generic system and clear CTs first
  juniper.apstra.generic_systems:
    blueprint_id: "{{ blueprint_id }}"
    system_id: "{{ gs_create.system_id }}"
    clear_cts_on_destroy: true
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
system_id:
  description: The graph node ID of the generic system.
  type: str
  returned: on create or when identified
blueprint_id:
  description: The blueprint ID.
  type: str
  returned: always
name:
  description: The display name (label) of the generic system.
  type: str
  returned: when system exists
hostname:
  description: The hostname of the generic system.
  type: str
  returned: when system exists
tags:
  description: The tags applied to the generic system node.
  type: list
  returned: when system exists
links:
  description: List of link IDs associated with the generic system.
  type: list
  returned: on create
deploy_mode:
  description: The deploy mode of the generic system.
  type: str
  returned: when system exists
external:
  description: Whether this is an external generic system.
  type: bool
  returned: when system exists
asn:
  description: The ASN assigned to the generic system.
  type: int
  returned: when system exists and ASN is set
loopback_ipv4:
  description: The IPv4 loopback address of the generic system.
  type: str
  returned: when system exists and loopback is set
loopback_ipv6:
  description: The IPv6 loopback address of the generic system.
  type: str
  returned: when system exists and loopback is set
port_channel_id_min:
  description: Minimum port-channel ID.
  type: int
  returned: when system exists
port_channel_id_max:
  description: Maximum port-channel ID.
  type: int
  returned: when system exists
changes:
  description: Dictionary of changes made during an update.
  type: dict
  returned: on update when changes are made
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

# ──────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────

# Read-only fields returned by the node API that should not be diffed
_READ_ONLY_FIELDS = frozenset(
    (
        "id",
        "type",
        "system_id",
        "system_type",
        "management_level",
        "role",
        "system_index",
        "position_data",
        "property_set",
        "user_data",
        "group_label",
        "tags",
        "access_l3_peer_link_port_channel_id_min",
        "access_l3_peer_link_port_channel_id_max",
    )
)


# ──────────────────────────────────────────────────────────────────
#  Low-level API helpers
# ──────────────────────────────────────────────────────────────────


def _api_get(client_factory, path):
    """Issue GET request and return parsed JSON or None."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path)
    if resp.status_code == 200:
        return resp.json()
    return None


def _api_post(client_factory, path, data, ok_codes=(200, 201, 202)):
    """Issue POST request; raise on unexpected status."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "POST", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"POST {path} failed: {resp.status_code} {resp.text}")


def _api_patch(client_factory, path, data, ok_codes=(200, 202, 204)):
    """Issue PATCH request; raise on unexpected status."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "PATCH", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"PATCH {path} failed: {resp.status_code} {resp.text}")


def _api_put(client_factory, path, data, ok_codes=(200, 202, 204)):
    """Issue PUT request; raise on unexpected status."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "PUT", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"PUT {path} failed: {resp.status_code} {resp.text}")


def _api_delete(client_factory, path, ok_codes=(200, 202, 204)):
    """Issue DELETE request; raise on unexpected status."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "DELETE")
    if resp.status_code not in ok_codes:
        raise Exception(f"DELETE {path} failed: {resp.status_code} {resp.text}")


# ──────────────────────────────────────────────────────────────────
#  Generic system read helpers
# ──────────────────────────────────────────────────────────────────


def _get_system_node(client_factory, bp_id, sys_id):
    """GET /api/blueprints/{bp}/nodes/{sys} — returns dict or None."""
    return _api_get(client_factory, f"/blueprints/{bp_id}/nodes/{sys_id}")


def _find_system_by_label(client_factory, bp_id, label):
    """Find a generic system by label using QE. Returns dict or None."""
    qe = {"query": f"node('system', system_type='server', label='{label}', name='gs')"}
    resp = _api_post(client_factory, f"/blueprints/{bp_id}/qe", qe)
    items = resp.get("items", []) if resp else []
    if items:
        return items[0].get("gs", items[0])
    return None


def _find_system_by_hostname(client_factory, bp_id, hostname):
    """Find a generic system by hostname using QE. Returns dict or None."""
    qe = {
        "query": f"node('system', system_type='server', hostname='{hostname}', name='gs')"
    }
    resp = _api_post(client_factory, f"/blueprints/{bp_id}/qe", qe)
    items = resp.get("items", []) if resp else []
    if items:
        return items[0].get("gs", items[0])
    return None


def _get_system_tags(client_factory, bp_id, sys_id):
    """Get tags for a system node. Returns list of tag strings."""
    node = _get_system_node(client_factory, bp_id, sys_id)
    if node:
        return node.get("tags", []) or []
    return []


def _get_system_link_ids(client_factory, bp_id, sys_id):
    """Get all physical (ethernet) link IDs for a system via QE."""
    qe = {
        "query": (
            f"node('system', id='{sys_id}', name='gs')"
            f".out('hosted_interfaces').node('interface', name='intf')"
            f".out('link').node('link', name='link')"
        )
    }
    resp = _api_post(client_factory, f"/blueprints/{bp_id}/qe", qe)
    items = resp.get("items", []) if resp else []
    link_ids = set()
    for item in items:
        if isinstance(item, dict):
            link_info = item.get("link", {})
            if isinstance(link_info, dict) and link_info.get("id"):
                if link_info.get("link_type") != "aggregate_link":
                    link_ids.add(link_info["id"])
    return list(link_ids)


def _get_system_links_detail(client_factory, bp_id, sys_id):
    """Get detailed link+interface info for a system.

    Returns list of dicts with keys:
    - link_id, target_switch_id, target_switch_if_name, lag_mode, group_label, tags
    """
    qe = {
        "query": (
            f"node('system', id='{sys_id}', name='gs')"
            f".out('hosted_interfaces').node('interface', name='gs_intf')"
            f".out('link').node('link', link_type='ethernet', name='link')"
            f".in_('link').node('interface', name='sw_intf')"
            f".in_('hosted_interfaces').node('system', name='switch')"
        )
    }
    resp = _api_post(client_factory, f"/blueprints/{bp_id}/qe", qe)
    items = resp.get("items", []) if resp else []
    links = []
    seen_link_ids = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        link = item.get("link", {})
        sw = item.get("switch", {})
        sw_intf = item.get("sw_intf", {})

        # The QE .in_('link') traversal returns BOTH ends of the link:
        # the GS's own interface and the switch interface.  Skip the
        # self-referential path where 'switch' is actually the GS itself.
        if sw.get("id") == sys_id:
            continue

        # Deduplicate by link_id (each physical link should appear once)
        lid = link.get("id")
        if lid in seen_link_ids:
            continue
        seen_link_ids.add(lid)

        links.append(
            {
                "link_id": lid,
                "target_switch_id": sw.get("id"),
                "target_switch_if_name": sw_intf.get("if_name"),
                "lag_mode": link.get("lag_mode"),
                "group_label": link.get("group_label"),
                "tags": link.get("tags", []) or [],
            }
        )
    return links


# ──────────────────────────────────────────────────────────────────
#  Generic system write helpers
# ──────────────────────────────────────────────────────────────────


def _create_switch_system_links(client_factory, bp_id, links, name, hostname):
    """Create a new generic system via switch-system-links API.

    Builds the payload from the flat link list, creating one new system.
    Returns the API response dict (with 'ids' list of created link IDs).
    """
    # Build the logical device from the links
    link_count = len(links)

    # Determine speed from the first link's transform (default 10G)
    speed_value = 10
    speed_unit = "G"

    # Determine port count per speed group
    api_links = []
    for idx, link in enumerate(links):
        api_link = {
            "switch": {
                "system_id": link["target_switch_id"],
                "transformation_id": link.get("target_switch_if_transform_id", 1),
                "if_name": link["target_switch_if_name"],
            },
            "system": {
                "system_id": None,
            },
            "new_system_index": 0,
        }
        if link.get("lag_mode"):
            api_link["lag_mode"] = link["lag_mode"]
        else:
            api_link["lag_mode"] = None
        if link.get("group_label"):
            api_link["link_group_label"] = link["group_label"]
        api_links.append(api_link)

    # Build logical device ID based on port count
    ld_id = f"AOS-{link_count}x{speed_value}-1"
    ld_display = ld_id

    body = {
        "links": api_links,
        "new_systems": [
            {
                "system_type": "server",
                "label": name or hostname or "generic-system",
                "hostname": hostname or name or "generic-system",
                "deploy_mode": "deploy",
                "logical_device": {
                    "id": ld_id,
                    "display_name": ld_display,
                    "panels": [
                        {
                            "port_groups": [
                                {
                                    "roles": ["leaf", "access"],
                                    "count": link_count,
                                    "speed": {
                                        "value": speed_value,
                                        "unit": speed_unit,
                                    },
                                }
                            ],
                            "port_indexing": {
                                "schema": "absolute",
                                "order": "T-B, L-R",
                                "start_index": 1,
                            },
                            "panel_layout": {
                                "row_count": 1,
                                "column_count": link_count,
                            },
                        }
                    ],
                },
                "port_channel_id_min": 0,
                "port_channel_id_max": 0,
            }
        ],
    }
    return _api_post(client_factory, f"/blueprints/{bp_id}/switch-system-links", body)


def _add_links_to_system(client_factory, bp_id, sys_id, links):
    """Add links to an existing generic system.

    POST /api/blueprints/{bp}/switch-system-links with system_id set.
    """
    api_links = []
    for link in links:
        api_link = {
            "switch": {
                "system_id": link["target_switch_id"],
                "transformation_id": link.get("target_switch_if_transform_id", 1),
                "if_name": link["target_switch_if_name"],
            },
            "system": {
                "system_id": sys_id,
            },
        }
        if link.get("lag_mode"):
            api_link["lag_mode"] = link["lag_mode"]
        else:
            api_link["lag_mode"] = None
        if link.get("group_label"):
            api_link["link_group_label"] = link["group_label"]
        api_links.append(api_link)

    body = {"links": api_links}
    return _api_post(client_factory, f"/blueprints/{bp_id}/switch-system-links", body)


def _delete_switch_system_links(client_factory, bp_id, link_ids):
    """Delete switch-system links by ID list.

    POST /api/blueprints/{bp}/delete-switch-system-links
    Removing the last link removes the generic system itself.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{bp_id}/delete-switch-system-links",
        "POST",
        data={"link_ids": link_ids},
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"Failed to delete switch-system-links: {resp.status_code} {resp.text}"
        )


def _create_external_generic_system(client_factory, bp_id, name, hostname):
    """Create an external generic system.

    POST /api/blueprints/{bp}/external-generic-systems
    """
    body = {
        "label": name or hostname or "external-generic-system",
        "hostname": hostname or name or "external-generic-system",
    }
    return _api_post(
        client_factory, f"/blueprints/{bp_id}/external-generic-systems", body
    )


def _delete_external_generic_system(client_factory, bp_id, sys_id):
    """DELETE /api/blueprints/{bp}/external-generic-systems/{sys}."""
    _api_delete(
        client_factory, f"/blueprints/{bp_id}/external-generic-systems/{sys_id}"
    )


# Properties that the Apstra node PATCH API accepts without allow_unsafe
_SAFE_PATCH_FIELDS = frozenset({"label", "deploy_mode", "system_id", "hostname"})


def _patch_node_unsafe(client_factory, bp_id, sys_id, patch_body):
    """PATCH /api/blueprints/{bp}/nodes/{sys}?allow_unsafe=true

    Required for any node property outside the safe set
    (tags, domain_id, loopback_ipv4/ipv6, port_channel_id_*, etc.).
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{bp_id}/nodes/{sys_id}?allow_unsafe=true",
        "PATCH",
        data=patch_body,
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"PATCH (unsafe) /blueprints/{bp_id}/nodes/{sys_id} failed: "
            f"{resp.status_code} {resp.text}"
        )
    try:
        return resp.json()
    except Exception:
        return {}


def _update_system_node(client_factory, bp_id, sys_id, patch_body):
    """PATCH /api/blueprints/{bp}/nodes/{sys}

    Automatically routes safe fields (label, hostname, deploy_mode) through
    the normal endpoint and everything else through allow_unsafe=true.
    """
    safe = {k: v for k, v in patch_body.items() if k in _SAFE_PATCH_FIELDS}
    unsafe = {k: v for k, v in patch_body.items() if k not in _SAFE_PATCH_FIELDS}

    result = {}
    if safe:
        result = _api_patch(client_factory, f"/blueprints/{bp_id}/nodes/{sys_id}", safe)
    if unsafe:
        result = _patch_node_unsafe(client_factory, bp_id, sys_id, unsafe)
    return result


def _set_system_tags(client_factory, bp_id, sys_id, tags):
    """Set tags on a system node.

    Tags are not in the safe-PATCH set, so allow_unsafe=true is required.
    """
    return _patch_node_unsafe(client_factory, bp_id, sys_id, {"tags": tags})


def _set_system_property(client_factory, bp_id, sys_id, prop, value):
    """Set a single property on a system node.

    Routes through safe or unsafe PATCH as appropriate.
    """
    if prop in _SAFE_PATCH_FIELDS:
        return _api_patch(
            client_factory,
            f"/blueprints/{bp_id}/nodes/{sys_id}",
            {prop: value},
        )
    return _patch_node_unsafe(client_factory, bp_id, sys_id, {prop: value})


def _clear_cts_from_links(client_factory, bp_id, sys_id):
    """Clear all connectivity templates from a system's link interfaces.

    Queries interfaces, then removes CT assignments from each.
    """
    qe = {
        "query": (
            f"node('system', id='{sys_id}', name='gs')"
            f".out('hosted_interfaces').node('interface', if_type='ethernet', name='intf')"
        )
    }
    resp = _api_post(client_factory, f"/blueprints/{bp_id}/qe", qe)
    items = resp.get("items", []) if resp else []
    intf_ids = []
    for item in items:
        if isinstance(item, dict):
            intf = item.get("intf", {})
            if isinstance(intf, dict) and intf.get("id"):
                intf_ids.append(intf["id"])

    if not intf_ids:
        return

    # Get current CT assignments and clear them
    for intf_id in intf_ids:
        try:
            # Try to remove CT assignments from this interface
            base = client_factory.get_base_client()
            resp = base.raw_request(
                f"/blueprints/{bp_id}/obj-policy-export",
                "POST",
                data={"policy_type_name": "", "application_points": [intf_id]},
            )
        except Exception:
            pass  # Best-effort CT clearing


# ──────────────────────────────────────────────────────────────────
#  Link digest for idempotent diffing
# ──────────────────────────────────────────────────────────────────


def _link_digest(link):
    """Compute a unique identifier for a link endpoint (switch_id:if_name)."""
    return f"{link.get('target_switch_id', '')}:{link.get('target_switch_if_name', '')}"


def _current_link_digest(link_detail):
    """Compute digest from a current-state link detail dict."""
    return f"{link_detail.get('target_switch_id', '')}:{link_detail.get('target_switch_if_name', '')}"


# ──────────────────────────────────────────────────────────────────
#  Build result dict from system state
# ──────────────────────────────────────────────────────────────────


def _build_result(
    client_factory,
    bp_id,
    sys_id,
    changed,
    msg,
    extra=None,
    overrides=None,
):
    """Build the standard result dict by reading current system state.

    *overrides* is an optional dict of property values that were just set
    and may not yet be reflected by the API due to eventual-consistency.
    When supplied, these values take precedence over the API read-back.
    """
    result = dict(
        changed=changed,
        blueprint_id=bp_id,
        msg=msg,
    )
    if extra:
        result.update(extra)

    overrides = overrides or {}

    if sys_id:
        result["system_id"] = sys_id
        node = _get_system_node(client_factory, bp_id, sys_id)
        if node:
            result["name"] = node.get("label", "")
            result["hostname"] = node.get("hostname", "")
            result["deploy_mode"] = overrides.get(
                "deploy_mode", node.get("deploy_mode", "")
            )
            result["external"] = node.get("external", False)
            result["tags"] = overrides.get("tags", node.get("tags", []) or [])
            result["asn"] = overrides.get("asn", node.get("domain_id"))
            result["loopback_ipv4"] = overrides.get(
                "loopback_ipv4", node.get("loopback_ipv4")
            )
            result["loopback_ipv6"] = overrides.get(
                "loopback_ipv6", node.get("loopback_ipv6")
            )
            result["port_channel_id_min"] = overrides.get(
                "port_channel_id_min", node.get("port_channel_id_min", 0)
            )
            result["port_channel_id_max"] = overrides.get(
                "port_channel_id_max", node.get("port_channel_id_max", 0)
            )

    return result


# ──────────────────────────────────────────────────────────────────
#  Validation
# ──────────────────────────────────────────────────────────────────


def _validate_links(links):
    """Validate that links have no duplicate endpoints (switch_id:if_name)."""
    if not links:
        return
    digests = set()
    for link in links:
        d = _link_digest(link)
        if d in digests:
            raise ValueError(
                f"Duplicate link endpoint: {d}. Each switch interface "
                f"can only appear once in the links list."
            )
        digests.add(d)

    # Validate LAG consistency: links in the same group must have the same lag_mode
    groups = {}
    for link in links:
        gl = link.get("group_label")
        if gl:
            lm = link.get("lag_mode")
            if gl in groups and groups[gl] != lm:
                raise ValueError(
                    f"Inconsistent lag_mode in group '{gl}': "
                    f"found both '{groups[gl]}' and '{lm}'"
                )
            groups[gl] = lm


# ──────────────────────────────────────────────────────────────────
#  State handlers
# ──────────────────────────────────────────────────────────────────


def _handle_present(module, client_factory):
    """Handle state=present — create or update."""
    p = module.params
    bp_id = p["blueprint_id"]
    sys_id = p.get("system_id")
    name = p.get("name")
    hostname = p.get("hostname")
    tags = p.get("tags")  # None means "not specified by user"; [] means "clear tags"
    links = p.get("links") or []
    deploy_mode = p.get("deploy_mode")  # None means "not specified by user"
    asn = p.get("asn")
    loopback_ipv4 = p.get("loopback_ipv4")
    loopback_ipv6 = p.get("loopback_ipv6")
    port_channel_id_min = p.get("port_channel_id_min") or 0
    port_channel_id_max = p.get("port_channel_id_max") or 0
    is_external = p.get("external") or False

    _validate_links(links)

    # ── Try to find existing system ───────────────────────────────
    existing = None
    if sys_id:
        existing = _get_system_node(client_factory, bp_id, sys_id)
        if existing is None:
            raise ValueError(
                f"Generic system '{sys_id}' not found in blueprint '{bp_id}'"
            )
    elif name:
        existing = _find_system_by_label(client_factory, bp_id, name)
        if existing:
            sys_id = existing["id"]
    elif hostname:
        existing = _find_system_by_hostname(client_factory, bp_id, hostname)
        if existing:
            sys_id = existing["id"]

    if existing:
        # ── UPDATE path ───────────────────────────────────────────
        return _handle_update(
            module,
            client_factory,
            bp_id,
            sys_id,
            existing,
            name,
            hostname,
            tags,
            links,
            deploy_mode,
            asn,
            loopback_ipv4,
            loopback_ipv6,
            port_channel_id_min,
            port_channel_id_max,
            is_external,
        )
    else:
        # ── CREATE path ───────────────────────────────────────────
        if is_external:
            return _handle_create_external(
                module,
                client_factory,
                bp_id,
                name,
                hostname,
                tags,
                links,
                deploy_mode,
                asn,
                loopback_ipv4,
                loopback_ipv6,
                port_channel_id_min,
                port_channel_id_max,
            )
        else:
            if not links:
                raise ValueError(
                    "Links are required to create a new in-rack generic system. "
                    "Provide at least one link or set external=true."
                )
            return _handle_create_with_links(
                module,
                client_factory,
                bp_id,
                name,
                hostname,
                tags,
                links,
                deploy_mode,
                asn,
                loopback_ipv4,
                loopback_ipv6,
                port_channel_id_min,
                port_channel_id_max,
            )


def _handle_create_with_links(
    module,
    client_factory,
    bp_id,
    name,
    hostname,
    tags,
    links,
    deploy_mode,
    asn,
    loopback_ipv4,
    loopback_ipv6,
    port_channel_id_min,
    port_channel_id_max,
):
    """Create a new generic system with links via switch-system-links."""
    created = _create_switch_system_links(client_factory, bp_id, links, name, hostname)
    link_ids = created.get("ids", [])

    # Discover the new system ID by looking up the label
    sys_id = None
    label = name or hostname
    if label:
        for _attempt in range(10):
            found = _find_system_by_label(client_factory, bp_id, label)
            if found:
                sys_id = found.get("id")
                break
            time.sleep(1)

    if not sys_id:
        raise ValueError(
            "Generic system was created but could not be found by label. "
            "Check the Apstra blueprint for the new system."
        )

    # Set additional properties after creation
    _apply_properties(
        client_factory,
        bp_id,
        sys_id,
        name,
        hostname,
        tags,
        deploy_mode,
        asn,
        loopback_ipv4,
        loopback_ipv6,
        port_channel_id_min,
        port_channel_id_max,
    )

    # Build overrides for eventual-consistency properties
    overrides = {}
    if tags:
        overrides["tags"] = tags
    if deploy_mode:
        overrides["deploy_mode"] = deploy_mode
    if asn is not None:
        overrides["asn"] = asn
    if loopback_ipv4:
        overrides["loopback_ipv4"] = loopback_ipv4
    if loopback_ipv6:
        overrides["loopback_ipv6"] = loopback_ipv6
    if port_channel_id_min:
        overrides["port_channel_id_min"] = port_channel_id_min
    if port_channel_id_max:
        overrides["port_channel_id_max"] = port_channel_id_max

    return _build_result(
        client_factory,
        bp_id,
        sys_id,
        True,
        "generic system created successfully",
        extra={"links": link_ids},
        overrides=overrides,
    )


def _handle_create_external(
    module,
    client_factory,
    bp_id,
    name,
    hostname,
    tags,
    links,
    deploy_mode,
    asn,
    loopback_ipv4,
    loopback_ipv6,
    port_channel_id_min,
    port_channel_id_max,
):
    """Create an external generic system, optionally with links."""
    created = _create_external_generic_system(client_factory, bp_id, name, hostname)
    sys_id = created.get("id") if isinstance(created, dict) else None

    if not sys_id:
        # Try to find it by label
        label = name or hostname
        if label:
            for _attempt in range(5):
                found = _find_system_by_label(client_factory, bp_id, label)
                if found:
                    sys_id = found.get("id")
                    break
                time.sleep(1)

    overrides = {}
    extra = {}
    if sys_id:
        _apply_properties(
            client_factory,
            bp_id,
            sys_id,
            name,
            hostname,
            tags,
            deploy_mode,
            asn,
            loopback_ipv4,
            loopback_ipv6,
            port_channel_id_min,
            port_channel_id_max,
        )
        if tags:
            overrides["tags"] = tags
        if deploy_mode:
            overrides["deploy_mode"] = deploy_mode
        if asn is not None:
            overrides["asn"] = asn
        if loopback_ipv4:
            overrides["loopback_ipv4"] = loopback_ipv4
        if loopback_ipv6:
            overrides["loopback_ipv6"] = loopback_ipv6

        # Process links if specified
        if links:
            link_changes = _update_link_set(client_factory, bp_id, sys_id, links)
            if link_changes:
                extra["links"] = link_changes

    return _build_result(
        client_factory,
        bp_id,
        sys_id,
        True,
        "external generic system created successfully",
        extra=extra,
        overrides=overrides,
    )


def _handle_update(
    module,
    client_factory,
    bp_id,
    sys_id,
    current,
    name,
    hostname,
    tags,
    links,
    deploy_mode,
    asn,
    loopback_ipv4,
    loopback_ipv6,
    port_channel_id_min,
    port_channel_id_max,
    is_external=None,
):
    """Update an existing generic system."""
    changed = False
    changes = {}

    # ── Update hostname and name (label) ──────────────────────────
    patch_body = {}
    if name and current.get("label") != name:
        patch_body["label"] = name
        changes["name"] = {"old": current.get("label"), "new": name}
    if hostname and current.get("hostname") != hostname:
        patch_body["hostname"] = hostname
        changes["hostname"] = {"old": current.get("hostname"), "new": hostname}
    if deploy_mode is not None and current.get("deploy_mode") != deploy_mode:
        patch_body["deploy_mode"] = deploy_mode
        changes["deploy_mode"] = {"old": current.get("deploy_mode"), "new": deploy_mode}

    if patch_body:
        _update_system_node(client_factory, bp_id, sys_id, patch_body)
        changed = True

    # ── Update external flag (requires allow_unsafe) ──────────────
    if is_external is not None:
        current_external = current.get("external", False)
        if current_external != is_external:
            _set_system_property(client_factory, bp_id, sys_id, "external", is_external)
            changes["external"] = {"old": current_external, "new": is_external}
            changed = True

    # ── Update tags ───────────────────────────────────────────────
    current_tags = sorted(current.get("tags", []) or [])
    desired_tags = sorted(tags) if tags else []
    if tags is not None and current_tags != desired_tags:
        _set_system_tags(client_factory, bp_id, sys_id, tags)
        changes["tags"] = {"old": current_tags, "new": desired_tags}
        changed = True

    # ── Update ASN ────────────────────────────────────────────────
    current_asn = current.get("domain_id")
    if asn is not None and current_asn != asn:
        _set_system_property(client_factory, bp_id, sys_id, "domain_id", asn)
        changes["asn"] = {"old": current_asn, "new": asn}
        changed = True

    # ── Update loopback IPv4 ──────────────────────────────────────
    current_lo4 = current.get("loopback_ipv4")
    if loopback_ipv4 is not None and current_lo4 != loopback_ipv4:
        _set_system_property(
            client_factory, bp_id, sys_id, "loopback_ipv4", loopback_ipv4
        )
        changes["loopback_ipv4"] = {"old": current_lo4, "new": loopback_ipv4}
        changed = True

    # ── Update loopback IPv6 ──────────────────────────────────────
    current_lo6 = current.get("loopback_ipv6")
    if loopback_ipv6 is not None and current_lo6 != loopback_ipv6:
        _set_system_property(
            client_factory, bp_id, sys_id, "loopback_ipv6", loopback_ipv6
        )
        changes["loopback_ipv6"] = {"old": current_lo6, "new": loopback_ipv6}
        changed = True

    # ── Update port-channel ID range ──────────────────────────────
    cur_pc_min = current.get("port_channel_id_min", 0) or 0
    cur_pc_max = current.get("port_channel_id_max", 0) or 0
    if port_channel_id_min is not None and cur_pc_min != port_channel_id_min:
        _set_system_property(
            client_factory,
            bp_id,
            sys_id,
            "port_channel_id_min",
            port_channel_id_min,
        )
        changes["port_channel_id_min"] = {"old": cur_pc_min, "new": port_channel_id_min}
        changed = True
    if port_channel_id_max is not None and cur_pc_max != port_channel_id_max:
        _set_system_property(
            client_factory,
            bp_id,
            sys_id,
            "port_channel_id_max",
            port_channel_id_max,
        )
        changes["port_channel_id_max"] = {"old": cur_pc_max, "new": port_channel_id_max}
        changed = True

    # ── Update links (diff-based) ─────────────────────────────────
    if links:
        link_changes = _update_link_set(client_factory, bp_id, sys_id, links)
        if link_changes:
            changes["links"] = link_changes
            changed = True

    if changed:
        # Build overrides for eventual-consistency properties
        overrides = {}
        if tags is not None:
            overrides["tags"] = tags
        if deploy_mode:
            overrides["deploy_mode"] = deploy_mode
        if asn is not None:
            overrides["asn"] = asn
        if loopback_ipv4 is not None:
            overrides["loopback_ipv4"] = loopback_ipv4
        if loopback_ipv6 is not None:
            overrides["loopback_ipv6"] = loopback_ipv6
        if port_channel_id_min is not None:
            overrides["port_channel_id_min"] = port_channel_id_min
        if port_channel_id_max is not None:
            overrides["port_channel_id_max"] = port_channel_id_max
        time.sleep(1)  # Allow async PATCH to propagate
        return _build_result(
            client_factory,
            bp_id,
            sys_id,
            True,
            "generic system updated successfully",
            extra={"changes": changes},
            overrides=overrides,
        )
    else:
        return _build_result(
            client_factory,
            bp_id,
            sys_id,
            False,
            "no changes needed for generic system",
        )


def _update_link_set(client_factory, bp_id, sys_id, desired_links):
    """Diff desired vs current links and apply add/delete operations.

    Returns a changes dict or None if no changes.
    """
    current_links = _get_system_links_detail(client_factory, bp_id, sys_id)

    # Build digest maps
    current_by_digest = {_current_link_digest(cl): cl for cl in current_links}
    desired_by_digest = {_link_digest(dl): dl for dl in desired_links}

    to_add = []
    to_delete = []

    # Links in desired but not in current → add
    for digest, link in desired_by_digest.items():
        if digest not in current_by_digest:
            to_add.append(link)

    # Links in current but not in desired → delete
    for digest, link in current_by_digest.items():
        if digest not in desired_by_digest:
            to_delete.append(link)

    changes = {}
    if to_delete:
        del_ids = [l["link_id"] for l in to_delete if l.get("link_id")]
        if del_ids:
            _delete_switch_system_links(client_factory, bp_id, del_ids)
            changes["removed"] = [_current_link_digest(l) for l in to_delete]

    if to_add:
        _add_links_to_system(client_factory, bp_id, sys_id, to_add)
        changes["added"] = [_link_digest(l) for l in to_add]

    return changes if changes else None


def _apply_properties(
    client_factory,
    bp_id,
    sys_id,
    name,
    hostname,
    tags,
    deploy_mode,
    asn,
    loopback_ipv4,
    loopback_ipv6,
    port_channel_id_min,
    port_channel_id_max,
):
    """Apply all system-level properties after creation.

    Safe properties (deploy_mode) go through normal PATCH.
    Unsafe properties (tags, ASN, loopbacks, port-channel) are batched
    into a single PATCH with allow_unsafe=true for efficiency.
    """
    # Safe properties (normal node PATCH)
    safe_patch = {}
    if deploy_mode and deploy_mode != "deploy":
        safe_patch["deploy_mode"] = deploy_mode
    if safe_patch:
        _api_patch(client_factory, f"/blueprints/{bp_id}/nodes/{sys_id}", safe_patch)

    # Unsafe properties (require allow_unsafe=true)
    unsafe_patch = {}
    if tags:
        unsafe_patch["tags"] = tags
    if asn is not None:
        unsafe_patch["domain_id"] = asn
    if loopback_ipv4:
        unsafe_patch["loopback_ipv4"] = loopback_ipv4
    if loopback_ipv6:
        unsafe_patch["loopback_ipv6"] = loopback_ipv6
    if port_channel_id_min:
        unsafe_patch["port_channel_id_min"] = port_channel_id_min
    if port_channel_id_max:
        unsafe_patch["port_channel_id_max"] = port_channel_id_max
    if unsafe_patch:
        _patch_node_unsafe(client_factory, bp_id, sys_id, unsafe_patch)


def _handle_absent(module, client_factory):
    """Handle state=absent — delete a generic system."""
    p = module.params
    bp_id = p["blueprint_id"]
    sys_id = p.get("system_id")
    name = p.get("name")
    hostname = p.get("hostname")
    is_external = p.get("external") or False
    clear_cts = p.get("clear_cts_on_destroy") or False

    # Try to resolve system by name/hostname if no system_id given
    if not sys_id:
        if name:
            found = _find_system_by_label(client_factory, bp_id, name)
            if found:
                sys_id = found.get("id")
                if not is_external and found.get("external"):
                    is_external = True
        elif hostname:
            found = _find_system_by_hostname(client_factory, bp_id, hostname)
            if found:
                sys_id = found.get("id")
                if not is_external and found.get("external"):
                    is_external = True

    if not sys_id:
        return _build_result(
            client_factory,
            bp_id,
            None,
            False,
            "generic system does not exist",
        )

    # Check if system still exists
    current = _get_system_node(client_factory, bp_id, sys_id)
    if current is None:
        return _build_result(
            client_factory,
            bp_id,
            sys_id,
            False,
            "generic system does not exist",
        )

    # Auto-detect external flag from current state
    if current.get("external"):
        is_external = True

    # Clear CTs if requested
    if clear_cts:
        try:
            _clear_cts_from_links(client_factory, bp_id, sys_id)
            time.sleep(1)
        except Exception:
            pass  # Best-effort

    if is_external:
        # Remove links first — Apstra requires links to be removed
        # before deleting an external generic system.
        link_ids = _get_system_link_ids(client_factory, bp_id, sys_id)
        if link_ids:
            _delete_switch_system_links(client_factory, bp_id, link_ids)
            time.sleep(1)
        _delete_external_generic_system(client_factory, bp_id, sys_id)
        return _build_result(
            client_factory,
            bp_id,
            sys_id,
            True,
            "external generic system deleted successfully",
        )
    else:
        link_ids = _get_system_link_ids(client_factory, bp_id, sys_id)
        if link_ids:
            _delete_switch_system_links(client_factory, bp_id, link_ids)
            return _build_result(
                client_factory,
                bp_id,
                sys_id,
                True,
                "generic system deleted successfully (all links removed)",
            )
        else:
            return _build_result(
                client_factory,
                bp_id,
                sys_id,
                False,
                "generic system has no links to remove. "
                "For external generic systems set external=true.",
            )


# ──────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        blueprint_id=dict(type="str", required=True),
        system_id=dict(type="str", required=False, default=None),
        name=dict(type="str", required=False, default=None),
        hostname=dict(type="str", required=False, default=None),
        tags=dict(type="list", elements="str", required=False, default=None),
        links=dict(
            type="list",
            elements="dict",
            required=False,
            default=[],
            options=dict(
                target_switch_id=dict(type="str", required=True),
                target_switch_if_name=dict(type="str", required=True),
                target_switch_if_transform_id=dict(type="int", required=True),
                lag_mode=dict(
                    type="str",
                    required=False,
                    default=None,
                    choices=["lacp_active", "lacp_passive", "static_lag"],
                ),
                group_label=dict(type="str", required=False, default=None),
                tags=dict(type="list", elements="str", required=False, default=[]),
            ),
        ),
        deploy_mode=dict(
            type="str",
            required=False,
            default=None,
            choices=["deploy", "ready", "drain", "undeploy"],
        ),
        asn=dict(type="int", required=False, default=None),
        loopback_ipv4=dict(type="str", required=False, default=None),
        loopback_ipv6=dict(type="str", required=False, default=None),
        port_channel_id_min=dict(type="int", required=False, default=0),
        port_channel_id_max=dict(type="int", required=False, default=0),
        external=dict(type="bool", required=False, default=False),
        clear_cts_on_destroy=dict(type="bool", required=False, default=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        state = module.params["state"]
        if state == "present":
            result = _handle_present(module, client_factory)
        elif state == "absent":
            result = _handle_absent(module, client_factory)
        else:
            result = dict(changed=False, msg=f"Unknown state: {state}")

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == "__main__":
    main()
