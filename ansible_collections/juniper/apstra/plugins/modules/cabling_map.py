#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

DOCUMENTATION = """
---
module: cabling_map

short_description: Manage and inspect the cabling map in an Apstra blueprint

version_added: "0.2.0"

author:
  - "Vamsi Gavini (@vgavini)"

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
    default: APSTRA_API_URL environment variable
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
    default: APSTRA_USERNAME environment variable
  password:
    description:
      - The Apstra password for authentication.
    type: str
    required: false
    default: APSTRA_PASSWORD environment variable
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
    default: APSTRA_AUTH_TOKEN environment variable
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
        C(system_node_id) (str) to filter results.
      - For C(lldp), optional key C(system_id) (str) to filter by system.
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
      system_node_id: "abc123"
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
links:
  description: >
    List of link objects returned by the operation.
    For C(gathered), contains the full cabling map links.
    For C(lldp), contains LLDP-discovered link data.
    For C(diff), contains links with differences.
    For C(present), contains the updated cabling map links.
  type: list
  returned: always
msg:
  description: A human-readable message describing what happened.
  type: str
  returned: always
"""


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


def _get_lldp(client_factory, blueprint_id, body):
    """
    GET /api/blueprints/{id}/cabling-map/lldp
    Optional body key: system_id (str).
    Returns list of link objects.
    """
    client = _get_blueprint_client(client_factory, blueprint_id)
    system_id = (body or {}).get("system_id")
    result = client.blueprints[blueprint_id].cabling_map.lldp.get(system_id=system_id)
    # SDK already extracts ['links'] and returns the list
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
    body = module.params.get("body") or {}
    links = _get_cabling_map(client_factory, blueprint_id, body)
    return dict(
        changed=False,
        links=links,
        msg=f"gathered {len(links)} cabling map link(s)",
    )


def _handle_lldp(module, client_factory, blueprint_id):
    """Return LLDP data from /cabling-map/lldp."""
    body = module.params.get("body") or {}
    links = _get_lldp(client_factory, blueprint_id, body)
    return dict(
        changed=False,
        links=links,
        msg=f"gathered LLDP data for {len(links)} link(s)",
    )


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
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
