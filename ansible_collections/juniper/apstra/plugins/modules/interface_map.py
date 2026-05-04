#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: interface_map

short_description: Manage interface map assignments in an Apstra blueprint

version_added: "0.2.0"

author:
  - "Vamsi Gavini (@vgavini)"

description:
  - This module manages interface map assignments within an Apstra
    blueprint.
  - Interface maps link blueprint switch nodes to device profiles that
    define port layout, speed, breakout, and naming.
  - Uses the Apstra interface-map-assignments API via the AOS SDK.
  - Provides full idempotency. Existing assignments are fetched and
    compared before patching.
  - Partial updates are supported. Only the nodes specified in
    C(assignments) are modified. Other nodes keep their current
    assignments.

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
      - Must contain C(blueprint) key with the blueprint ID or label.
    type: dict
    required: true
    suboptions:
      blueprint:
        description:
          - The ID or label of the blueprint in which to manage
            interface map assignments.
        type: str
        required: true
  body:
    description:
      - A dictionary containing the interface map assignments.
      - Must contain an C(assignments) key mapping blueprint node IDs
        (or node labels) to interface map IDs (or interface map names).
      - Node keys that are not UUIDs are resolved by label via a
        blueprint graph query.
      - Interface map values that are not UUIDs are resolved by label
        from the design interface-maps catalog.
      - Values may be C(null) or an empty string to clear an assignment.
      - "Example: C(assignments: {spine1: Juniper_vJunos-switch_vJunos})"
    type: dict
    required: true
  state:
    description:
      - Desired state of the interface map assignments.
      - C(present) assigns the specified interface maps to nodes.
      - C(absent) clears the interface map assignments for the
        specified nodes (sets them to null).
    type: str
    required: false
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Assign interface maps to blueprint nodes ──────────────────────

- name: Assign interface maps to spine and leaf switches
  juniper.apstra.interface_map:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      assignments:
        "{{ spine_node_id }}": "Juniper_vJunos-switch_vJunos"
        "{{ leaf_node_id }}": "Juniper_vJunos-switch_vJunos"
    state: present

# ── Assign using node labels instead of UUIDs ─────────────────────

- name: Assign interface maps by node label and IM label
  juniper.apstra.interface_map:
    id:
      blueprint: "my-blueprint"
    body:
      assignments:
        spine1: "my_spine_ifmap"
        leaf1: "my_leaf_ifmap"
    state: present

# ── Assign different maps per role ────────────────────────────────

- name: Assign interface maps based on device role
  juniper.apstra.interface_map:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      assignments: "{{ im_assignments }}"
    state: present

# ── Clear interface map assignments ───────────────────────────────

- name: Clear interface map for a specific node
  juniper.apstra.interface_map:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      assignments:
        "{{ node_id }}": null
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
assignments:
  description: The final interface map assignments after the operation.
  type: dict
  returned: always
  sample:
    node_id_1: "Juniper_vJunos-switch_vJunos"
    node_id_2: "Arista_vEOS-lab_vEOS-lab"
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


def _get_assignments(client_factory, blueprint_id):
    """GET /api/blueprints/{id}/interface-map-assignments."""
    client = _get_l3clos_client(client_factory)
    result = client.blueprints[blueprint_id].get_im_assignments()
    if result and isinstance(result, dict):
        return result
    return {}


def _patch_assignments(client_factory, blueprint_id, assignments):
    """PATCH /api/blueprints/{id}/interface-map-assignments."""
    client = _get_l3clos_client(client_factory)
    data = {"assignments": assignments}
    client.blueprints[blueprint_id].patch_im_assignments(data)


def _compute_changes(current, desired, state):
    """Compute what needs to change.

    Returns:
        tuple: (patch_body, has_changes) — the patch dict and whether
        there are any actual changes needed.
    """
    patch = {}
    has_changes = False

    for node_id, im_id in desired.items():
        current_value = current.get(node_id)

        if state == "absent":
            # Clear assignment (set to null)
            if current_value is not None and current_value != "":
                patch[node_id] = None
                has_changes = True
        else:
            # state == "present" — assign the interface map
            if im_id is None or im_id == "":
                # Treat null/empty in present state as clearing
                if current_value is not None and current_value != "":
                    patch[node_id] = None
                    has_changes = True
            elif current_value != im_id:
                patch[node_id] = im_id
                has_changes = True

    return patch, has_changes


def _resolve_node_label(client_factory, blueprint_id, label):
    """Resolve a blueprint node label to its graph node ID.

    Queries the blueprint graph for a ``system`` node with the given
    label and returns its ID.  Returns ``None`` if not found.
    """
    obj = client_factory.get_by_label(blueprint_id, "system", label)
    if obj:
        return obj.id if hasattr(obj, "id") else obj.get("id")
    return None


_UUID_RE = __import__("re").compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    __import__("re").IGNORECASE,
)


def _resolve_im_label(client_factory, im_ref):
    """Resolve an interface-map label to its UUID.

    If *im_ref* already looks like a UUID it is returned as-is.
    Otherwise all design interface maps are listed and the one whose
    ``label`` matches is returned.  Returns the original *im_ref*
    unchanged if no match is found.
    """
    if not im_ref or _UUID_RE.match(str(im_ref)):
        return im_ref

    client = _get_l3clos_client(client_factory)
    result = client.request("/design/interface-maps", method="GET")
    items = (result or {}).get("items", [])
    for item in items:
        if item.get("label") == im_ref:
            return item["id"]

    # Not found — return as-is and let the API report the error
    return im_ref


def _resolve_assignments(module, client_factory, blueprint_id, desired, current):
    """Resolve human-readable names in *desired* assignments to IDs.

    * Node keys that don't appear in the *current* assignments dict
      are treated as labels and resolved via a blueprint graph query.
    * Interface-map values that are not UUIDs are resolved by label
      from the design interface-maps catalog.

    Returns a new dict with all node keys and IM values resolved to IDs.
    """
    # Pre-resolve unique IM labels (avoid repeated API calls)
    im_cache = {}
    resolved = {}
    for node_ref, im_ref in desired.items():
        # ── Resolve node key ─────────────────────────────────────
        if node_ref in current:
            # Already a known graph node ID
            node_id = node_ref
        else:
            # Try to resolve as a label
            resolved_id = _resolve_node_label(client_factory, blueprint_id, node_ref)
            if resolved_id:
                module.debug(f"Resolved node label '{node_ref}' → '{resolved_id}'")
                node_id = resolved_id
            else:
                # Not in current and not found by label — pass through
                # and let the API handle the error if it's invalid
                node_id = node_ref

        # ── Resolve IM value ─────────────────────────────────────
        if im_ref and im_ref not in im_cache:
            resolved_im = _resolve_im_label(client_factory, im_ref)
            if resolved_im != im_ref:
                module.debug(
                    f"Resolved interface-map label '{im_ref}' → '{resolved_im}'"
                )
            im_cache[im_ref] = resolved_im

        resolved[node_id] = im_cache.get(im_ref, im_ref)

    return resolved


# ──────────────────────────────────────────────────────────────────
#  State handlers
# ──────────────────────────────────────────────────────────────────


def _handle_present(module, client_factory):
    """Handle state=present — assign interface maps."""
    p = module.params
    id_param = p["id"] or {}
    blueprint_id = id_param.get("blueprint")
    if blueprint_id:
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
        id_param["blueprint"] = blueprint_id
    body = p["body"] or {}
    desired = body.get("assignments", {})

    current = _get_assignments(client_factory, blueprint_id)

    # Resolve human-readable node labels and imap names to IDs
    desired = _resolve_assignments(
        module, client_factory, blueprint_id, desired, current
    )

    patch, has_changes = _compute_changes(current, desired, "present")

    if not has_changes:
        return dict(
            changed=False,
            assignments=current,
            msg="interface map assignments already up to date",
        )

    _patch_assignments(client_factory, blueprint_id, patch)

    # Build final state from current + patch (avoids SDK cache staleness)
    final = dict(current)
    final.update(patch)
    return dict(
        changed=True,
        assignments=final,
        msg=f"interface map assignments updated for {len(patch)} node(s)",
    )


def _handle_absent(module, client_factory):
    """Handle state=absent — clear interface map assignments."""
    p = module.params
    id_param = p["id"] or {}
    blueprint_id = id_param.get("blueprint")
    if blueprint_id:
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
        id_param["blueprint"] = blueprint_id
    body = p["body"] or {}
    desired = body.get("assignments", {})

    current = _get_assignments(client_factory, blueprint_id)

    # Resolve human-readable node labels and imap names to IDs
    desired = _resolve_assignments(
        module, client_factory, blueprint_id, desired, current
    )

    patch, has_changes = _compute_changes(current, desired, "absent")

    if not has_changes:
        return dict(
            changed=False,
            assignments=current,
            msg="interface map assignments already cleared",
        )

    _patch_assignments(client_factory, blueprint_id, patch)

    # Build final state from current + patch (avoids SDK cache staleness)
    final = dict(current)
    final.update(patch)
    return dict(
        changed=True,
        assignments=final,
        msg=f"interface map assignments cleared for {len(patch)} node(s)",
    )


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=True),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        state = module.params["state"]
        if state == "present":
            result = _handle_present(module, client_factory)
        elif state == "absent":
            result = _handle_absent(module, client_factory)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
