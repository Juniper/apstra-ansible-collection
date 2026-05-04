#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: cabling_map

short_description: Manage and inspect the cabling map in an Apstra blueprint

version_added: "0.2.0"

author:
  - "Vijay Gavini (@vgavini)"

description:
  - Provides read and write access to the Apstra cabling map for a blueprint.
  - Supports both C(two_stage_l3clos) (datacenter) and C(freeform) AOS reference
    designs.
  - Four operations are available via the C(state) parameter.
  - C(gathered) — return the full cabling map from
    C(/experience/web/cabling-map).
  - C(lldp) — return raw LLDP data per system from
    C(/cabling-map/lldp).
  - C(diff) — return the diff between LLDP data and the intended
    configuration from C(/cabling-map/diff).
  - C(present) — update link configuration (speed, interface names,
    IP addresses) via C(PATCH /cabling-map).

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
  state:
    description:
      - The operation to perform.
      - C(gathered) returns the full cabling map (default).
      - C(lldp) returns LLDP data per system.
      - C(diff) returns the diff between LLDP and intended config.
      - C(present) updates one or more links via PATCH.
    type: str
    required: false
    default: gathered
    choices: [gathered, lldp, diff, present]
  id:
    description:
      - Identifies the blueprint scope.
      - Must contain the C(blueprint) key with the blueprint ID or label.
    type: dict
    required: true
    suboptions:
      blueprint:
        description:
          - The ID or label of the blueprint.
        type: str
        required: true
  body:
    description:
      - Parameters body for the operation.
      - For C(present), requires a C(links) list of link objects to update.
        Each link object must contain at least an C(id) or C(endpoints) key.
      - For C(gathered), optional keys are C(aggregate_links) (bool) and
        C(system_node_id) (str, UUID or system label) to filter results.
      - For C(lldp), optional key C(system_id) (str) to filter by system.
        C(update_cabling_map) (bool, default false) syncs the cabling map
        with LLDP-discovered links. C(create_new_generic) (bool, default
        false) creates generic systems found in LLDP but missing from the
        blueprint.
      - For C(diff), optional key C(check_interface_map) (bool, default true)
        to include interface map check.
    type: dict
    required: false
    default: {}
"""

EXAMPLES = """
# ── Gather full cabling map ───────────────────────────────────────

- name: Get full cabling map
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: gathered
  register: cm

- name: Show cabling map links
  ansible.builtin.debug:
    var: cm.links

# ── Gather with filters ───────────────────────────────────────────

- name: Get cabling map for a specific system
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: gathered
    body:
      system_node_id: "spine1"      # label or UUID
      aggregate_links: true
  register: cm_filtered

# ── Get LLDP data ─────────────────────────────────────────────────

- name: Get LLDP data for all systems
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: lldp
  register: lldp_data

- name: Get LLDP data for a specific system
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: lldp
    body:
      system_id: "0C00DC7D8D00"
  register: lldp_system

# ── Sync cabling map with LLDP data ──────────────────────────────

- name: Update cabling map from LLDP discoveries
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: lldp
    body:
      update_cabling_map: true
  register: lldp_sync

# ── Create new generic systems from LLDP ──────────────────────────

- name: Create generic systems found by LLDP but missing from blueprint
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: lldp
    body:
      create_new_generic: true
  register: new_generics

- name: Sync cabling map and create new generics in one pass
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: lldp
    body:
      update_cabling_map: true
      create_new_generic: true
  register: full_sync

# ── Get LLDP vs intended diff ─────────────────────────────────────

- name: Get cabling map diff (LLDP vs intended)
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: diff
  register: cm_diff

# ── Update link configuration ─────────────────────────────────────

- name: Update interface name on a link
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: present
    body:
      links:
        - endpoints:
            - interface:
                id: "wZWAFd5z3k4XbkOf-g"
                if_name: "ge-0/0/2"
            - interface:
                id: "KcvvS_lwlG1mgPSIeA"
                if_name: "ge-0/0/1"
  register: patch_result

- name: Update multiple links with IP addresses
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-blueprint"
    state: present
    body:
      links:
        - endpoints:
            - interface:
                id: "op0XiI2mKpOtieV8vg"
                if_name: "ge-0/0/2"
                ipv4_addr: "10.10.0.4/31"
            - interface:
                id: "LVIFCDchlHEV4V-K9g"
                if_name: "ge-0/0/0"
                ipv4_addr: "10.10.0.5/31"
  register: patch_result

# ── Works with freeform blueprints ───────────────────────────────

- name: Get cabling map for a freeform blueprint
  juniper.apstra.cabling_map:
    id:
      blueprint: "my-freeform-blueprint"
    state: gathered
  register: cm_freeform
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
nodes:
  description: >
    Dictionary of per-system LLDP data keyed by node ID.
    Each value contains the LLDP telemetry reported by that system
    (hostname, management IP, system ID, interfaces, etc.).
    Only returned when C(state=lldp).
  type: dict
  returned: when state is lldp
links:
  description: >
    List of link objects returned by the operation.
    For C(gathered), contains the full cabling map links.
    For C(lldp), contains LLDP-discovered link data.
    For C(diff), contains links with differences.
    For C(present), contains the updated cabling map links.
  type: list
  returned: always
new_generics:
  description: >
    List of new generic system items that were created (or would be
    created in check mode). Only returned when C(state=lldp) with
    C(body.create_new_generic=true) and items exist.
  type: list
  returned: when state is lldp and create_new_generic is true
msg:
  description: A human-readable message describing what happened.
  type: str
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_system_node_id,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_cabling_map import (
    get_lldp_nodes,
)


# ──────────────────────────────────────────────────────────────────
#  SDK helpers
# ──────────────────────────────────────────────────────────────────


def _get_blueprint_client(client_factory, blueprint_id):
    """
    Return the appropriate blueprint client (l3clos or freeform),
    auto-detecting the design type from the blueprint.
    """
    return client_factory._get_blueprint_client(blueprint_id)


def _get_cabling_map(client_factory, blueprint_id, body):
    """
    GET /api/blueprints/{id}/experience/web/cabling-map
    Optional body keys: aggregate_links (bool), system_node_id (str).
    Returns list of link objects.
    """
    client = _get_blueprint_client(client_factory, blueprint_id)
    params = {}
    if body:
        if body.get("aggregate_links") is not None:
            params["aggregate_links"] = str(body["aggregate_links"]).lower()
        if body.get("system_node_id"):
            params["system_node_id"] = body["system_node_id"]

    bp = client.blueprints[blueprint_id]
    if params:
        result = bp.experience.web.cabling_map.get(params=params)
    else:
        result = bp.experience.web.cabling_map.get()

    # SDK returns list of links directly
    if isinstance(result, list):
        return result
    # Fallback: dict with 'links' key
    return result.get("links", []) if isinstance(result, dict) else []


def _get_lldp_links(client_factory, blueprint_id, body):
    """
    GET /api/blueprints/{id}/cabling-map/lldp  (links only, via SDK)
    Optional body key: system_id (str).
    Returns list of link objects.
    """
    client = _get_blueprint_client(client_factory, blueprint_id)
    system_id = (body or {}).get("system_id")
    result = client.blueprints[blueprint_id].cabling_map.lldp.get(system_id=system_id)
    if isinstance(result, list):
        return result
    return result.get("links", []) if isinstance(result, dict) else []


def _get_diff(client_factory, blueprint_id, body):
    """
    GET /api/blueprints/{id}/cabling-map/diff
    Optional body key: check_interface_map (bool, default true).
    Returns list of link objects.
    """
    client = _get_blueprint_client(client_factory, blueprint_id)
    params = {}
    if body and body.get("check_interface_map") is not None:
        params["check_interface_map"] = str(body["check_interface_map"]).lower()

    bp_cm_diff = client.blueprints[blueprint_id].cabling_map.diff
    if params:
        result = bp_cm_diff.get(params=params)
    else:
        result = bp_cm_diff.get()

    # SDK extracts ['links'] and returns the list
    if isinstance(result, list):
        return result
    return result.get("links", []) if isinstance(result, dict) else []


def _update_cabling_map(client_factory, blueprint_id, body):
    """
    PATCH /api/blueprints/{id}/cabling-map
    body must contain 'links' list.
    Returns the API response.
    """
    client = _get_blueprint_client(client_factory, blueprint_id)
    links = body.get("links", [])
    if not links:
        raise ValueError("'body.links' must be a non-empty list for state=present")
    return client.blueprints[blueprint_id].cabling_map.update({"links": links})


# ──────────────────────────────────────────────────────────────────
#  State handlers
# ──────────────────────────────────────────────────────────────────


def _handle_gathered(module, client_factory, blueprint_id):
    """Return the full cabling map from /experience/web/cabling-map."""
    body = dict(module.params.get("body") or {})
    if body.get("system_node_id"):
        body["system_node_id"] = resolve_system_node_id(
            client_factory, blueprint_id, body["system_node_id"]
        )
    links = _get_cabling_map(client_factory, blueprint_id, body)
    return dict(
        changed=False,
        links=links,
        msg=f"gathered {len(links)} cabling map link(s)",
    )


def _handle_lldp(module, client_factory, blueprint_id):
    """Return LLDP data from /cabling-map/lldp.

    Optional body keys:
      - system_id (str): filter by system MAC
      - update_cabling_map (bool): sync cabling map with LLDP links
      - create_new_generic (bool): create generic systems discovered via LLDP
    """
    body = module.params.get("body") or {}
    system_id = (body or {}).get("system_id")
    update_cm = bool(body.get("update_cabling_map", False))
    create_ng = bool(body.get("create_new_generic", False))

    # SDK provides links; nodes require raw_request (not in SDK)
    links = _get_lldp_links(client_factory, blueprint_id, body)
    nodes = get_lldp_nodes(client_factory, blueprint_id, system_id=system_id)

    changed = False
    actions = []
    new_generics = []

    # ── update_cabling_map ────────────────────────────────────────
    if update_cm and links:
        if module.check_mode:
            actions.append(f"would update cabling map with {len(links)} link(s)")
            changed = True
        else:
            _update_cabling_map(client_factory, blueprint_id, {"links": links})
            actions.append(f"updated cabling map with {len(links)} link(s)")
            changed = True

    # ── create_new_generic ────────────────────────────────────────
    if create_ng:
        client = _get_blueprint_client(client_factory, blueprint_id)
        bp = client.blueprints[blueprint_id]
        items = bp.cabling_map.new_generics.get() or []
        if items:
            if module.check_mode:
                actions.append(f"would create {len(items)} new generic system(s)")
                changed = True
                new_generics = items
            else:
                for item in items:
                    bp.add_switch_system_link(item)
                actions.append(f"created {len(items)} new generic system(s)")
                changed = True
                new_generics = items
        else:
            actions.append("no new generic systems to create")

    msg_parts = [f"gathered LLDP data: {len(nodes)} node(s), {len(links)} link(s)"]
    if actions:
        msg_parts.extend(actions)

    result = dict(
        changed=changed,
        nodes=nodes,
        links=links,
        msg="; ".join(msg_parts),
    )
    if new_generics:
        result["new_generics"] = new_generics
    return result


def _handle_diff(module, client_factory, blueprint_id):
    """Return LLDP vs intended diff from /cabling-map/diff."""
    body = module.params.get("body") or {}
    links = _get_diff(client_factory, blueprint_id, body)
    return dict(
        changed=False,
        links=links,
        msg=f"gathered cabling map diff: {len(links)} link(s) with differences",
    )


def _handle_present(module, client_factory, blueprint_id):
    """Update link configuration via PATCH /cabling-map."""
    body = module.params.get("body") or {}
    links = body.get("links", [])
    if not links:
        raise ValueError(
            "'body.links' is required and must be non-empty for state=present"
        )

    if module.check_mode:
        return dict(
            changed=True,
            links=links,
            msg=f"check mode: would update {len(links)} link(s)",
        )

    _update_cabling_map(client_factory, blueprint_id, body)

    # Fetch the updated cabling map for return value
    updated_links = _get_cabling_map(client_factory, blueprint_id, {})
    return dict(
        changed=True,
        links=updated_links,
        msg=f"updated cabling map: {len(links)} link(s) patched",
    )


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


_STATE_HANDLERS = {
    "gathered": _handle_gathered,
    "lldp": _handle_lldp,
    "diff": _handle_diff,
    "present": _handle_present,
}


def main():
    object_module_args = dict(
        state=dict(
            type="str",
            required=False,
            default="gathered",
            choices=["gathered", "lldp", "diff", "present"],
        ),
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False, default={}),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False, links=[])

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        p = module.params
        id_param = p["id"] or {}
        blueprint_id = id_param.get("blueprint")
        if not blueprint_id:
            raise ValueError("'id.blueprint' is required")
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)

        state = p["state"]
        handler = _STATE_HANDLERS[state]
        result = handler(module, client_factory, blueprint_id)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
