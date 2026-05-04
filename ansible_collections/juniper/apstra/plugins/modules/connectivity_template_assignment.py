#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: connectivity_template_assignment

short_description: Assign or unassign Connectivity Templates to application points

version_added: "0.1.0"

author:
  - "Vamsi Gavini (@vgavini)"

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
      - Identifies the blueprint and connectivity template.
      - Must contain C(blueprint) key with the blueprint ID.
      - Must contain either C(ct_id) (UUID) or C(ct_name) (label) to
        identify the Connectivity Template.
    type: dict
    required: true
    suboptions:
      blueprint:
        description:
          - The ID or label of the Apstra blueprint.
          - C(blueprint_id) is accepted as an alias for this key.
        required: true
        type: str
      ct_id:
        description:
          - The UUID or name (label) of the Connectivity Template to assign.
          - If a non-UUID value is supplied it is automatically resolved
            to a UUID by looking up the CT name in the blueprint.
          - Either C(ct_id) or C(ct_name) must be provided.
        required: false
        type: str
      ct_name:
        description:
          - The name (label) of the Connectivity Template to assign.
          - Used to look up the CT when C(ct_id) is not provided.
        required: false
        type: str
  body:
    description:
      - The assignment payload.
      - Must contain C(application_point_ids) list of application-point
        references to assign the CT to (when state is present) or unassign
        from (when state is absent).
      - |
        Each entry may be:
        - A raw blueprint graph node ID string
          (e.g. C(G31G9dCSVcDS9PoeYg)).
        - A colon-separated shorthand string C("<system_label>:<if_name>")
          (e.g. C("leaf1:ge-0/0/3") or C("leaf1:ae1")) that is resolved
          to the interface node ID via a QE graph query.
        - A resolution dict with C(system) and C(if_name) keys that is
          resolved to the interface node ID via a QE graph query.
    type: dict
    required: true
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
# ── Assign using colon-shorthand (system:if_name) strings ────────────

- name: Assign CT using system:if_name shorthand
  juniper.apstra.connectivity_template_assignment:
    id:
      blueprint: "{{ blueprint_id }}"
      ct_name: "NewVN2"
    body:
      application_point_ids:
        - "leaf1:ge-0/0/3"
        - "leaf1:ae1"
        - "leaf2:ae1"
        - "leaf3:ge-0/0/2"
    state: present

# ── Assign by CT ID using raw node IDs ───────────────────────────────

- name: Assign CT to multiple interfaces (raw node IDs)
  juniper.apstra.connectivity_template_assignment:
    id:
      blueprint: "{{ blueprint_id }}"
      ct_id: "{{ ct_id }}"
    body:
      application_point_ids:
        - "G31G9dCSVcDS9PoeYg"
        - "x2LgjvQJTCNdPBQL9A"
    state: present

# ── Assign by CT name using human-readable interface refs ─────────────

- name: Assign BGP-2-SRX CT using system label + interface name
  juniper.apstra.connectivity_template_assignment:
    id:
      blueprint: "{{ blueprint_id }}"
      ct_name: "BGP-2-SRX"
    body:
      application_point_ids:
        - system: "leaf1"
          if_name: "ge-0/0/1"
        - system: "leaf2"
          if_name: "ge-0/0/1"
    state: present

# ── Mixed refs: raw IDs and human-readable in the same list ───────────

- name: Assign CT — mixed raw IDs and interface dicts
  juniper.apstra.connectivity_template_assignment:
    id:
      blueprint: "{{ blueprint_id }}"
      ct_name: "My-CT"
    body:
      application_point_ids:
        - "G31G9dCSVcDS9PoeYg"
        - system: "spine1"
          if_name: "et-0/0/0"
    state: present

# ── Unassign CT from interfaces ───────────────────────────────────────

- name: Unassign CT from interfaces
  juniper.apstra.connectivity_template_assignment:
    id:
      blueprint: "{{ blueprint_id }}"
      ct_id: "{{ ct_id }}"
    body:
      application_point_ids:
        - system: "leaf1"
          if_name: "ge-0/0/1"
    state: absent
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

import re
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    AOS_IMPORT_ERROR,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_application_point_ids,
)

if not AOS_IMPORT_ERROR:
    from aos.sdk.reference_design.extension.endpoint_policy import (
        generator as ct_gen,
    )


# ── Helper functions ──────────────────────────────────────────────────────────

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_uuid(value):
    """Return True if *value* looks like a UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)."""
    return bool(_UUID_RE.match(str(value))) if value else False


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

    Returns a tuple:
      - states:       dict {interface_id: state_string}
                      ALL valid application-point interface IDs are present,
                      even those never assigned (state defaults to "unused").
      - valid_ap_ids: set of all valid application-point interface IDs for
                      this CT (used for input validation).
    """
    app_points = (
        ep_client.blueprints[blueprint_id]
        .endpoint_policies[ct_id]
        .application_points.get()
    )
    states = {}
    valid_ap_ids = set()
    _walk_app_points_tree(app_points, ct_id, states, valid_ap_ids)
    return states, valid_ap_ids


def _walk_app_points_tree(node, ct_id, states, valid_ap_ids):
    """Recursively walk the app-points tree and extract interface states.

    Every interface node found is added to *valid_ap_ids* regardless of
    whether the CT has been assigned to it.  The state for each interface
    defaults to ``"unused"`` and is overwritten when a matching policy
    entry is found.
    """
    if not isinstance(node, dict):
        return

    if node.get("type") == "interface":
        node_id = node.get("id")
        if node_id:
            valid_ap_ids.add(node_id)
            # Default to unused; overwrite if the CT has a policy entry here.
            ct_state = "unused"
            for pol in node.get("policies", []):
                if pol.get("policy") == ct_id:
                    ct_state = pol.get("state", "unused")
                    break
            states[node_id] = ct_state

    # Walk children
    children = node.get("children", [])
    if isinstance(children, list):
        for child in children:
            _walk_app_points_tree(child, ct_id, states, valid_ap_ids)

    # Also walk nested 'application_points' key (top-level response)
    ap = node.get("application_points")
    if isinstance(ap, dict):
        for child in ap.get("children", []):
            _walk_app_points_tree(child, ct_id, states, valid_ap_ids)


# ── Main module logic ─────────────────────────────────────────────────────────


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
        # Instantiate client
        client_factory = ApstraClientFactory.from_params(module)
        ep_client = client_factory.get_endpointpolicy_client()

        # Validate params
        id_param = module.params["id"] or {}
        blueprint_id = id_param.get("blueprint") or id_param.get("blueprint_id")
        if blueprint_id:
            blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
            id_param["blueprint"] = blueprint_id
        ct_id = id_param.get("ct_id")
        ct_name = id_param.get("ct_name")
        body = module.params["body"] or {}
        application_point_ids_raw = body.get("application_point_ids", [])
        state = module.params["state"]

        # ── Resolve application point IDs (human-readable → node ID) ──
        application_point_ids = resolve_application_point_ids(
            client_factory, blueprint_id, application_point_ids_raw
        )
        # Map resolved UUID → original reference string for error reporting.
        _id_to_ref = {
            uid: raw
            for uid, raw in zip(application_point_ids, application_point_ids_raw)
            if uid != raw  # only store entries where resolution changed the value
        }

        # ── Resolve CT ID ─────────────────────────────────────────────
        # If ct_id is provided but is not a UUID, treat it as a name.
        if ct_id and not _is_uuid(ct_id):
            ct_name = ct_name or ct_id
            ct_id = None

        if not ct_id:
            if ct_name:
                ct_id = _find_ct_by_name(ep_client, blueprint_id, ct_name)
                if not ct_id:
                    raise ValueError(
                        f"Connectivity Template with name '{ct_name}' "
                        f"not found in blueprint '{blueprint_id}'"
                    )
            else:
                raise ValueError("Either 'ct_id' (UUID) or 'ct_name' is required")

        if not application_point_ids:
            result["msg"] = "No application_point_ids specified, nothing to do"
            module.exit_json(**result)
            return

        # ── Get current state ─────────────────────────────────────────
        current_states, valid_ap_ids = _get_current_assignments(
            ep_client, blueprint_id, ct_id
        )

        # ── Validate resolved IDs against the CT’s application-points tree ──
        invalid_ids = [i for i in application_point_ids if i not in valid_ap_ids]
        if invalid_ids:
            # Build a human-readable representation for each invalid ID.
            invalid_display = [
                f"{_id_to_ref[i]!r} (resolved: {i})" if i in _id_to_ref else repr(i)
                for i in invalid_ids
            ]
            # Detect whether any failing ref looks like a LAG on an individual
            # ESI leaf member (e.g. "leaf1:ae1") so we can give a targeted hint.
            _lag_hint = ""
            for raw in [_id_to_ref.get(i, "") for i in invalid_ids]:
                if re.search(r"(?<!/)[^/]+:ae\d+", str(raw), re.IGNORECASE):
                    _lag_hint = (
                        " Hint: ae/LAG interfaces on ESI leaf-pairs must be "
                        "referenced as the leaf-pair, not individual leaves "
                        "(e.g. 'leaf1/leaf2:ae1' instead of 'leaf1:ae1' and "
                        "'leaf2:ae1')."
                    )
                    break
            raise ValueError(
                f"The following interfaces are not valid application points "
                f"for CT '{ct_id}' in blueprint '{blueprint_id}': "
                f"{invalid_display}.{_lag_hint}"
            )

        # ── Determine needed changes ──────────────────────────────────
        to_apply = []
        to_unapply = []

        # Apstra reports assignment state as "used-directly" (directly assigned)
        # or "used-indirectly" (inherited via a parent group).  Any "used*" state
        # means the CT is already active on that application point.
        _USED_STATES = {"used", "used-directly", "used-indirectly"}

        if state == "present":
            for intf_id in application_point_ids:
                current = current_states.get(intf_id, "unused")
                if current not in _USED_STATES:
                    to_apply.append(intf_id)
        else:  # absent
            for intf_id in application_point_ids:
                current = current_states.get(intf_id, "unused")
                if current in _USED_STATES:
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
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
