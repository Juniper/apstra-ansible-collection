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
  id:
    description:
      - Identifies the blueprint scope.
      - Must contain C(blueprint) key with the blueprint ID.
    type: dict
    required: true
    suboptions:
      blueprint:
        description:
          - The ID of the blueprint in which to manage interface map
            assignments.
        type: str
        required: true
  body:
    description:
      - A dictionary containing the interface map assignments.
      - Must contain an C(assignments) key mapping blueprint node IDs
        to interface map IDs.
      - Values may be C(null) or an empty string to clear an assignment.
      - "Example: C(assignments: {node_id_1: Juniper_vJunos-switch_vJunos})"
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


# ──────────────────────────────────────────────────────────────────
#  SDK helpers
# ──────────────────────────────────────────────────────────────────


def _get_l3clos_client(client_factory, blueprint_id):
    """Return the l3clos client scoped to the blueprint."""
    return client_factory.get_l3clos_client()


def _get_assignments(client_factory, blueprint_id):
    """GET /api/blueprints/{id}/interface-map-assignments."""
    client = _get_l3clos_client(client_factory, blueprint_id)
    result = client.blueprints[blueprint_id].get_im_assignments()
    if result and "assignments" in result:
        return result["assignments"]
    return {}


def _patch_assignments(client_factory, blueprint_id, assignments):
    """PATCH /api/blueprints/{id}/interface-map-assignments."""
    client = _get_l3clos_client(client_factory, blueprint_id)
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


# ──────────────────────────────────────────────────────────────────
#  State handlers
# ──────────────────────────────────────────────────────────────────


def _handle_present(module, client_factory):
    """Handle state=present — assign interface maps."""
    p = module.params
    id_param = p["id"] or {}
    blueprint_id = id_param.get("blueprint")
    body = p["body"] or {}
    desired = body.get("assignments", {})

    current = _get_assignments(client_factory, blueprint_id)
    patch, has_changes = _compute_changes(current, desired, "present")

    if not has_changes:
        return dict(
            changed=False,
            assignments=current,
            msg="interface map assignments already up to date",
        )

    _patch_assignments(client_factory, blueprint_id, patch)

    # Re-read to return final state
    final = _get_assignments(client_factory, blueprint_id)
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
    body = p["body"] or {}
    desired = body.get("assignments", {})

    current = _get_assignments(client_factory, blueprint_id)
    patch, has_changes = _compute_changes(current, desired, "absent")

    if not has_changes:
        return dict(
            changed=False,
            assignments=current,
            msg="interface map assignments already cleared",
        )

    _patch_assignments(client_factory, blueprint_id, patch)

    final = _get_assignments(client_factory, blueprint_id)
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
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
