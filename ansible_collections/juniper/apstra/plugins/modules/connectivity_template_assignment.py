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
    AOS_IMPORT_ERROR,
)

if not AOS_IMPORT_ERROR:
    from aos.sdk.reference_design.extension.endpoint_policy import (
        generator as ct_gen,
    )

DOCUMENTATION = """
---
module: connectivity_template_assignment

short_description: Assign or unassign Connectivity Templates to application points

version_added: "0.1.0"

author:
  - "Juniper Networks"

description:
  - This module assigns or unassigns Connectivity Templates (CTs) to
    application points (interfaces) within an Apstra blueprint.
  - Application points are identified by their node IDs (interface IDs
    from the blueprint graph).
  - Uses the C(obj-policy-batch-apply) API for efficient bulk
    assignment operations.
  - The module is idempotent — it reads the current assignment state
    and only makes changes when the desired state differs.
  - Use the C(connectivity_template) module to create CTs before
    assigning them.

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
      - The ID of the Apstra blueprint.
    required: true
    type: str
  ct_id:
    description:
      - The UUID of the Connectivity Template to assign.
      - Either C(ct_id) or C(ct_name) must be provided.
    required: false
    type: str
  ct_name:
    description:
      - The name (label) of the Connectivity Template to assign.
      - Used to look up the CT when C(ct_id) is not provided.
    required: false
    type: str
  application_point_ids:
    description:
      - A list of interface node IDs to assign the CT to (when state
        is present) or unassign from (when state is absent).
      - These are the graph node IDs of interfaces in the blueprint,
        obtainable from the application-points API or from graph queries.
    required: true
    type: list
    elements: str
  state:
    description:
      - Desired state of the CT assignments.
      - C(present) assigns the CT to the listed application points.
      - C(absent) unassigns the CT from the listed application points.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Assign by CT ID ──────────────────────────────────────────────────

# Assign a CT to a single interface by CT ID
- name: Assign CT to one interface
  juniper.apstra.connectivity_template_assignment:
    blueprint_id: "{{ blueprint_id }}"
    ct_id: "{{ ct_id }}"
    application_point_ids:
      - "{{ interface_id }}"
    state: present

# Assign a CT to multiple interfaces at once (bulk)
- name: Assign CT to multiple interfaces
  juniper.apstra.connectivity_template_assignment:
    blueprint_id: "{{ blueprint_id }}"
    ct_id: "{{ ct_id }}"
    application_point_ids:
      - "G31G9dCSVcDS9PoeYg"
      - "x2LgjvQJTCNdPBQL9A"
      - "Hk9PqW3mTfNcRbYx1Z"
    state: present

# ── Assign by CT name ────────────────────────────────────────────────

# Assign a CT by name lookup (no need to know the CT UUID)
- name: Assign BGP-2-SRX CT to interfaces
  juniper.apstra.connectivity_template_assignment:
    blueprint_id: "{{ blueprint_id }}"
    ct_name: "BGP-2-SRX"
    application_point_ids:
      - "{{ interface_id }}"
    state: present

# ── Using registered output from connectivity_template ───────────────

# First create the CT, then assign it in a follow-up task
- name: Create the CT
  juniper.apstra.connectivity_template:
    blueprint_id: "{{ blueprint_id }}"
    name: "VLAN-100-Access"
    type: interface
    primitives:
      virtual_network_singles:
        vlan100:
          vn_node_id: "{{ virtual_network_id }}"
    state: present
  register: ct_result

- name: Assign the CT using registered output
  juniper.apstra.connectivity_template_assignment:
    blueprint_id: "{{ blueprint_id }}"
    ct_id: "{{ ct_result.ct_id }}"
    application_point_ids:
      - "{{ interface_id_1 }}"
      - "{{ interface_id_2 }}"
    state: present

# ── Unassign (remove) CT from interfaces ─────────────────────────────

# Unassign a CT from specific interfaces by CT ID
- name: Unassign CT from interfaces
  juniper.apstra.connectivity_template_assignment:
    blueprint_id: "{{ blueprint_id }}"
    ct_id: "{{ ct_id }}"
    application_point_ids:
      - "G31G9dCSVcDS9PoeYg"
    state: absent

# Unassign a CT by name
- name: Unassign CT from interfaces by name
  juniper.apstra.connectivity_template_assignment:
    blueprint_id: "{{ blueprint_id }}"
    ct_name: "BGP-2-SRX"
    application_point_ids:
      - "{{ interface_id }}"
    state: absent

# ── Idempotent re-run ────────────────────────────────────────────────

# Running the same assign again produces changed=false
- name: Assign CT (idempotent — no change on second run)
  juniper.apstra.connectivity_template_assignment:
    blueprint_id: "{{ blueprint_id }}"
    ct_name: "VLAN-100-Access"
    application_point_ids:
      - "{{ interface_id }}"
    state: present
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
applied:
  description: List of interface IDs that were newly assigned.
  type: list
  returned: when state is present and changes are made
unapplied:
  description: List of interface IDs that were newly unassigned.
  type: list
  returned: when state is absent and changes are made
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


# ── Helper functions ──────────────────────────────────────────────────────────


def _find_ct_by_name(ep_client, blueprint_id, name):
    """
    Find a visible CT (top-level batch) by name (label).

    Returns ct_id or None.
    """
    all_eps = ep_client.blueprints[blueprint_id].endpoint_policies.list()
    if isinstance(all_eps, dict):
        all_eps = all_eps.get("endpoint_policies", [])

    for ep in all_eps:
        if (
            ep.get("visible") is True
            and ep.get("policy_type_name") == "batch"
            and ep.get("label") == name
        ):
            return ep.get("id")
    return None


def _get_current_assignments(ep_client, blueprint_id, ct_id):
    """
    Get the current assignment states for a CT by walking the
    application-points tree.

    Returns a dict: {interface_id: "used"|"unused"}
    """
    app_points = (
        ep_client.blueprints[blueprint_id]
        .endpoint_policies[ct_id]
        .application_points.get()
    )
    states = {}
    _walk_app_points_tree(app_points, ct_id, states)
    return states


def _walk_app_points_tree(node, ct_id, states):
    """Recursively walk the app-points tree and extract interface states."""
    if not isinstance(node, dict):
        return

    # Check if this node has policies for our CT
    if node.get("type") == "interface":
        for pol in node.get("policies", []):
            if pol.get("policy") == ct_id:
                states[node["id"]] = pol.get("state", "unused")

    # Walk children
    children = node.get("children", [])
    if isinstance(children, list):
        for child in children:
            _walk_app_points_tree(child, ct_id, states)

    # Also walk nested 'application_points' key (top-level response)
    ap = node.get("application_points")
    if isinstance(ap, dict):
        for child in ap.get("children", []):
            _walk_app_points_tree(child, ct_id, states)


# ── Main module logic ─────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        blueprint_id=dict(type="str", required=True),
        ct_id=dict(type="str", required=False),
        ct_name=dict(type="str", required=False),
        application_point_ids=dict(type="list", elements="str", required=True),
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
        # Instantiate client
        client_factory = ApstraClientFactory.from_params(module)
        ep_client = client_factory.get_endpointpolicy_client()

        # Validate params
        blueprint_id = module.params["blueprint_id"]
        ct_id = module.params.get("ct_id")
        ct_name = module.params.get("ct_name")
        application_point_ids = module.params["application_point_ids"]
        state = module.params["state"]

        # ── Resolve CT ID ─────────────────────────────────────────────
        if not ct_id:
            if ct_name:
                ct_id = _find_ct_by_name(ep_client, blueprint_id, ct_name)
                if not ct_id:
                    raise ValueError(
                        f"Connectivity Template with name '{ct_name}' "
                        f"not found in blueprint '{blueprint_id}'"
                    )
            else:
                raise ValueError("Either 'ct_id' or 'ct_name' is required")

        if not application_point_ids:
            result["msg"] = "No application_point_ids specified, nothing to do"
            module.exit_json(**result)
            return

        # ── Get current state ─────────────────────────────────────────
        current_states = _get_current_assignments(ep_client, blueprint_id, ct_id)

        # ── Determine needed changes ──────────────────────────────────
        to_apply = []
        to_unapply = []

        if state == "present":
            for intf_id in application_point_ids:
                current = current_states.get(intf_id, "unused")
                if current != "used":
                    to_apply.append(intf_id)
        else:  # absent
            for intf_id in application_point_ids:
                current = current_states.get(intf_id, "unused")
                if current == "used":
                    to_unapply.append(intf_id)

        # ── Apply changes via batch API ───────────────────────────────
        if to_apply or to_unapply:
            dto = ct_gen.gen_apply_unapply(
                ct_id,
                app_point_ids_apply=to_apply if to_apply else None,
                app_point_ids_unapply=to_unapply if to_unapply else None,
            )
            payload = ct_gen.create_batch_apply_unapply_ct(dto)
            ep_client.blueprints[blueprint_id].obj_policy_batch_apply.patch(payload)

            result["changed"] = True
            if to_apply:
                result["applied"] = to_apply
            if to_unapply:
                result["unapplied"] = to_unapply
            result["msg"] = (
                f"CT assignments updated: "
                f"{len(to_apply)} applied, {len(to_unapply)} unapplied"
            )
        else:
            result["changed"] = False
            result["msg"] = "All application points already in desired state"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
