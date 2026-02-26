#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import time
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    AOS_IMPORT_ERROR,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ct_primitives import (
    CT_TYPES,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ct_validator import (
    validate_primitives,
    CTValidationError,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ct_builder import (
    build_ct_payload,
    get_ct_id_from_hierarchy,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ct_parser import (
    parse_ct_export,
    normalize_for_compare,
)


DOCUMENTATION = """
---
module: connectivity_template

short_description: Manage Connectivity Templates in Apstra blueprints

version_added: "0.1.0"

author:
  - "Juniper Networks"

description:
  - This module allows you to create, update, and delete Connectivity
    Templates (CTs) within an Apstra blueprint.
  - A Connectivity Template is a declarative specification of network
    primitives (IP Link, BGP Peering, Routing Policy, etc.) that can
    be assigned to application points (interfaces, SVIs, loopbacks,
    protocol endpoints, or systems).
  - Every CT has a B(type) that determines which primitives may be used
    and which kind of application point it targets.
  - Primitives are specified as a dict-of-named-dicts keyed by the
    B(plural) primitive type name.  Child primitives are nested inside
    their parent as additional dict keys.
  - The module automatically builds the internal batch/pipeline/primitive
    hierarchy required by the Apstra API.
  - Idempotent by C(name).  If a CT with the same name already exists,
    the module compares the desired primitives with the current state
    (via C(obj-policy-export)) and updates only when there are
    differences.
  - This module manages the CT definition only.  Use the
    C(connectivity_template_assignment) module to assign CTs to
    application points.

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
  id:
    description:
      - A dict identifying the target blueprint and optionally an
        existing Connectivity Template.
    required: true
    type: dict
    suboptions:
      blueprint:
        description:
          - The ID of the Apstra blueprint.
        required: true
        type: str
      ct_id:
        description:
          - The UUID of an existing Connectivity Template.
          - When provided, the module operates on this specific CT
            instead of looking up by C(name) in C(body).
        required: false
        type: str
  body:
    description:
      - A dict containing the Connectivity Template specification.
    required: false
    type: dict
    suboptions:
      name:
        description:
          - The display name of the Connectivity Template.
          - Used as the unique identifier for idempotent operations.
          - Required when C(state=present).
        required: false
        type: str
      type:
        description:
          - The type of Connectivity Template, which determines which
            primitives are allowed and which application point type the
            CT targets.
          - Required when C(state=present).
        required: false
        type: str
        choices:
          - interface
          - svi
          - loopback
          - protocol_endpoint
          - system
      description:
        description:
          - An optional description for the Connectivity Template.
        required: false
        type: str
        default: ""
      tags:
        description:
          - A list of tags to apply to the CT.
        required: false
        type: list
        elements: str
      primitives:
        description:
          - A dict-of-named-dicts keyed by B(plural) primitive type name.
          - Each top-level key is a primitive type (e.g. C(ip_links),
            C(virtual_network_singles), C(bgp_peering_generic_systems)).
          - Under each type key is a dict of named instances.
          - Each instance is a dict of type-specific attributes passed
            directly to the Apstra API.
          - Child primitives are nested as additional dict keys using
            their plural type name (e.g. C(bgp_peering_generic_systems)
            inside an C(ip_links) instance).
          - "Supported primitive types: C(ip_links), C(virtual_network_singles),
            C(virtual_network_multiples), C(bgp_peering_generic_systems),
            C(bgp_peering_ip_endpoints), C(routing_policies),
            C(static_routes), C(custom_static_routes),
            C(dynamic_bgp_peerings), C(routing_zone_constraints)."
        required: false
        type: dict
  state:
    description:
      - Desired state of the Connectivity Template.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Interface CT type examples ────────────────────────────────────────

# Interface CT: IP Link + BGP Peering + Routing Policy (full nesting)
- name: Create BGP-to-SRX Connectivity Template
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "BGP-2-SRX"
      type: interface
      description: "CT for external router connectivity"
      tags:
        - prod
        - border
      primitives:
        ip_links:
          srx_link:
            security_zone: "{{ routing_zone_id }}"
            interface_type: tagged
            vlan_id: 100
            ipv4_addressing_type: numbered
            ipv6_addressing_type: none
            bgp_peering_generic_systems:
              srx_peer:
                bfd: false
                ipv4_safi: true
                ipv6_safi: false
                ttl: 2
                session_addressing_ipv4: addressed
                session_addressing_ipv6: link_local
                peer_from: interface
                peer_to: interface_or_ip_endpoint
                neighbor_asn_type: dynamic
                routing_policies:
                  default_rp:
                    rp_to_attach: "{{ routing_policy_id }}"
    state: present
  register: ct_result

# Interface CT: IP Link with Static Route child
- name: Create IP Link with Static Route CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Static-Route-Link"
      type: interface
      primitives:
        ip_links:
          static_link:
            security_zone: "{{ routing_zone_id }}"
            interface_type: tagged
            vlan_id: 200
            ipv4_addressing_type: numbered
            ipv6_addressing_type: none
            static_routes:
              default_route:
                network: "0.0.0.0/0"
                share_ip_endpoint: false
                routing_policies:
                  static_rp: {}
    state: present

# Interface CT: IP Link with Custom Static Route child
- name: Create IP Link with Custom Static Route CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Custom-Static-Link"
      type: interface
      primitives:
        ip_links:
          custom_link:
            security_zone: "{{ routing_zone_id }}"
            interface_type: untagged
            ipv4_addressing_type: numbered
            ipv6_addressing_type: none
            custom_static_routes:
              mgmt_route:
                network: "10.0.0.0/8"
                next_hop: next_hop_ip
    state: present

# Interface CT: IP Link with Routing Policy (direct — no BGP/static in between)
- name: Create IP Link with direct Routing Policy CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "IP-Link-Direct-RP"
      type: interface
      primitives:
        ip_links:
          direct_rp_link:
            security_zone: "{{ routing_zone_id }}"
            interface_type: tagged
            vlan_id: 150
            ipv4_addressing_type: numbered
            ipv6_addressing_type: none
            routing_policies:
              export_filter:
                rp_to_attach: "{{ routing_policy_id }}"
    state: present

# Interface CT: Virtual Network (Single) — simple VLAN access
- name: Create VN Single CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "VLAN-100-Access"
      type: interface
      primitives:
        virtual_network_singles:
          vlan100:
            vn_node_id: "{{ virtual_network_id }}"
    state: present

# Interface CT: Virtual Network (Multiple) — trunk with multiple VLANs
- name: Create VN Multiple CT (trunk)
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Trunk-VLANs"
      type: interface
      primitives:
        virtual_network_multiples:
          trunk_vlans:
            tagged_vn_node_ids:
              - "{{ vn_id_1 }}"
              - "{{ vn_id_2 }}"
            untagged_vn_node_id: "{{ native_vn_id }}"
    state: present

# Interface CT: Routing Zone Constraint
- name: Create Routing Zone Constraint CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "RZ-Constraint-Intf"
      type: interface
      primitives:
        routing_zone_constraints:
          allow_default_only:
            routing_zone_constraint_mode: allow
            constraints:
              - "{{ routing_zone_id }}"
    state: present

# Interface CT: Custom Static Route (top-level)
- name: Create Custom Static Route CT for interface
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Custom-Static-Intf"
      type: interface
      primitives:
        custom_static_routes:
          default_gw:
            network: "0.0.0.0/0"
            next_hop: next_hop_ip
    state: present

# Interface CT: Multiple primitives in one CT
- name: Create CT with both IP Link and Routing Zone Constraint
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Multi-Primitive-CT"
      type: interface
      primitives:
        ip_links:
          server_link:
            security_zone: "{{ routing_zone_id }}"
            interface_type: tagged
            vlan_id: 300
            ipv4_addressing_type: numbered
            ipv6_addressing_type: none
        routing_zone_constraints:
          rz_limit:
            routing_zone_constraint_mode: allow
            constraints:
              - "{{ routing_zone_id }}"
    state: present

# ── SVI CT type examples ─────────────────────────────────────────────

# SVI CT: BGP Peering (Generic System) with Routing Policy
- name: Create SVI BGP CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "SVI-BGP-Peering"
      type: svi
      primitives:
        bgp_peering_generic_systems:
          external_peer:
            bfd: true
            ipv4_safi: true
            ipv6_safi: false
            ttl: 2
            session_addressing_ipv4: addressed
            session_addressing_ipv6: link_local
            peer_from: interface
            peer_to: interface_or_ip_endpoint
            neighbor_asn_type: dynamic
            routing_policies:
              export_rp:
                rp_to_attach: "{{ routing_policy_id }}"
    state: present

# SVI CT: Dynamic BGP Peering
- name: Create SVI Dynamic BGP CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "SVI-Dynamic-BGP"
      type: svi
      primitives:
        dynamic_bgp_peerings:
          auto_peer:
            ipv4_enabled: true
            ipv6_enabled: false
            ttl: 1
            session_addressing_ipv4: addressed
            session_addressing_ipv6: link_local
            bfd: false
            password: ""
            routing_policies:
              bgp_rp: {}
    state: present

# SVI CT: Static Route
- name: Create SVI Static Route CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "SVI-Static-Route"
      type: svi
      primitives:
        static_routes:
          default_route:
            network: "0.0.0.0/0"
            share_ip_endpoint: false
    state: present

# SVI CT: Virtual Network (Single)
- name: Create SVI VN Single CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "SVI-VN-Single"
      type: svi
      primitives:
        virtual_network_singles:
          svi_vlan:
            vn_node_id: "{{ virtual_network_id }}"
    state: present

# SVI CT: Routing Zone Constraint
- name: Create SVI Routing Zone Constraint CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "SVI-RZ-Constraint"
      type: svi
      primitives:
        routing_zone_constraints:
          svi_rz_limit:
            routing_zone_constraint_mode: deny
            constraints:
              - "{{ routing_zone_id }}"
    state: present

# ── Loopback CT type examples ────────────────────────────────────────

# Loopback CT: BGP Peering (IP Endpoint) with Routing Policy
- name: Create Loopback BGP IP Endpoint CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Loopback-BGP"
      type: loopback
      primitives:
        bgp_peering_ip_endpoints:
          lo0_peer:
            ipv4_safi: true
            ipv6_safi: false
            bfd: false
            ttl: 2
            session_addressing_ipv4: addressed
            session_addressing_ipv6: link_local
            password: ""
            routing_policies:
              lo_rp: {}
    state: present

# Loopback CT: Static Route
- name: Create Loopback Static Route CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Loopback-Static"
      type: loopback
      primitives:
        static_routes:
          lo_static:
            network: "192.168.1.0/24"
            share_ip_endpoint: false
    state: present

# Loopback CT: Routing Zone Constraint
- name: Create Loopback Routing Zone Constraint CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Loopback-RZ-Constraint"
      type: loopback
      primitives:
        routing_zone_constraints:
          lo_rz_limit:
            routing_zone_constraint_mode: allow
            constraints:
              - "{{ routing_zone_id }}"
    state: present

# ── Protocol Endpoint CT type examples ───────────────────────────────

# Protocol Endpoint CT: BGP Peering (IP Endpoint)
- name: Create Protocol Endpoint BGP CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Proto-EP-BGP"
      type: protocol_endpoint
      primitives:
        bgp_peering_ip_endpoints:
          ep_peer:
            ipv4_safi: true
            ipv6_safi: false
            bfd: true
            ttl: 1
            session_addressing_ipv4: addressed
            session_addressing_ipv6: link_local
            routing_policies:
              ep_rp:
                rp_to_attach: "{{ routing_policy_id }}"
    state: present

# Protocol Endpoint CT: Routing Zone Constraint
- name: Create Protocol Endpoint RZ Constraint CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "Proto-EP-RZ-Constraint"
      type: protocol_endpoint
      primitives:
        routing_zone_constraints:
          ep_rz_limit:
            routing_zone_constraint_mode: allow
            constraints:
              - "{{ routing_zone_id }}"
    state: present

# ── System CT type examples ──────────────────────────────────────────

# System CT: Custom Static Route
- name: Create System Custom Static Route CT
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "System-Static-Route"
      type: system
      primitives:
        custom_static_routes:
          sys_default:
            network: "0.0.0.0/0"
            next_hop: next_hop_ip
            routing_policies:
              sys_rp: {}
    state: present

# ── Update and delete examples ───────────────────────────────────────

# Update an existing CT by name (idempotent — re-run detects no change)
- name: Update BGP-2-SRX CT (change VLAN)
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "BGP-2-SRX"
      type: interface
      description: "Updated CT — new VLAN"
      primitives:
        ip_links:
          srx_link:
            security_zone: "{{ routing_zone_id }}"
            interface_type: tagged
            vlan_id: 200
            ipv4_addressing_type: numbered
            ipv6_addressing_type: none
    state: present

# Delete a CT by name
- name: Delete Connectivity Template by name
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
    body:
      name: "BGP-2-SRX"
    state: absent

# Delete a CT by ID (using registered output from create)
- name: Delete Connectivity Template by ID
  juniper.apstra.connectivity_template:
    id:
      blueprint: "{{ blueprint_id }}"
      ct_id: "{{ ct_result.ct_id }}"
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
ct_id:
  description: The UUID of the Connectivity Template.
  returned: when state is present
  type: str
  sample: "b016fec0-b439-45a4-bcf4-94b481f6005e"
connectivity_template:
  description: The parsed Connectivity Template object.
  type: dict
  returned: when state is present
  contains:
    name:
      description: The CT display name.
      type: str
    description:
      description: The CT description.
      type: str
    tags:
      description: Tags applied to the CT.
      type: list
    primitives:
      description: The primitives in dict-of-named-dicts format.
      type: dict
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


# ── Helper functions ──────────────────────────────────────────────────────────


def _find_ct_by_name(ep_client, blueprint_id, name):
    """
    Find a visible CT (top-level batch) by name (label).

    Uses the endpoint_policies list (fast) to locate by label, then
    returns the parsed export (rich) for comparison.

    Returns
    -------
    tuple(str, dict) or (None, None)
        ``(ct_id, parsed_export)``
    """
    all_eps = ep_client.blueprints[blueprint_id].endpoint_policies.list()
    if isinstance(all_eps, dict):
        all_eps = all_eps.get("endpoint_policies", [])

    ct_id = None
    for ep in all_eps:
        if (
            ep.get("visible") is True
            and ep.get("policy_type_name") == "batch"
            and ep.get("label") == name
        ):
            ct_id = ep.get("id")
            break

    if ct_id is None:
        return None, None

    # Fetch the full export for this CT
    export_data = ep_client.blueprints[blueprint_id].obj_policy_export[ct_id].get()
    parsed = parse_ct_export(export_data)
    return ct_id, parsed


def _export_ct(ep_client, blueprint_id, ct_id):
    """Export and parse a CT by ID."""
    export_data = ep_client.blueprints[blueprint_id].obj_policy_export[ct_id].get()
    return parse_ct_export(export_data)


def _get_ct_assignments(ep_client, blueprint_id, ct_id):
    """Get the list of application point IDs that have this CT assigned.

    Returns a list of application-point IDs (interface node IDs) where the
    given *ct_id* is currently applied.  Walks the
    ``endpoint-policies/{ct_id}/application-points`` tree.
    """
    try:
        app_points = (
            ep_client.blueprints[blueprint_id]
            .endpoint_policies[ct_id]
            .application_points.get()
        )
        states = {}
        _walk_ct_app_points(app_points, ct_id, states)
        return [
            intf_id for intf_id, state in states.items() if state.startswith("used")
        ]
    except Exception:
        return []


def _walk_ct_app_points(node, ct_id, states):
    """Recursively walk the app-points tree and extract interface states."""
    if not isinstance(node, dict):
        return

    if node.get("type") == "interface":
        for pol in node.get("policies", []):
            if pol.get("policy") == ct_id:
                states[node["id"]] = pol.get("state", "unused")

    for child in node.get("children", []):
        _walk_ct_app_points(child, ct_id, states)

    ap = node.get("application_points")
    if isinstance(ap, dict):
        for child in ap.get("children", []):
            _walk_ct_app_points(child, ct_id, states)


def _unassign_ct(ep_client, blueprint_id, ct_id, app_point_ids):
    """Remove CT assignment from given application points."""
    if not app_point_ids:
        return
    from aos.sdk.reference_design.extension.endpoint_policy import (
        generator as ct_gen,
    )

    dto = ct_gen.gen_apply_unapply(
        ct_id,
        app_point_ids_unapply=app_point_ids,
    )
    payload = ct_gen.create_batch_apply_unapply_ct(dto)
    ep_client.blueprints[blueprint_id].obj_policy_batch_apply.patch(payload)


def _reassign_ct(ep_client, blueprint_id, new_ct_id, app_point_ids):
    """Re-apply CT to previously assigned application points."""
    if not app_point_ids:
        return
    from aos.sdk.reference_design.extension.endpoint_policy import (
        generator as ct_gen,
    )

    dto = ct_gen.gen_apply_unapply(
        new_ct_id,
        app_point_ids_apply=app_point_ids,
    )
    payload = ct_gen.create_batch_apply_unapply_ct(dto)
    ep_client.blueprints[blueprint_id].obj_policy_batch_apply.patch(payload)


def _refresh_rp_bindings(ep_client, blueprint_id, hierarchy):
    """PATCH routing-policy primitives so the Apstra UI renders them.

    The ``obj-policy-import`` batch API stores ``rp_to_attach`` correctly
    as a text attribute but does not create the internal graph edge that
    the UI needs to populate the "Routing Policy" dropdown.  A follow-up
    PATCH on each AttachExistingRoutingPolicy primitive re-writes the
    same value through the per-primitive API path which does create the
    graph edge.

    Parameters
    ----------
    ep_client : endpointPolicyClient
        The endpoint policy SDK client.
    blueprint_id : str
        The blueprint ID.
    hierarchy : list[dict]
        The policy hierarchy returned by ``ct_gen.create_ct_with_hierarchy()``.
    """
    rp_type = "AttachExistingRoutingPolicy"
    for pol in hierarchy:
        if pol.get("policy_type_name") == rp_type and pol.get("attributes", {}).get(
            "rp_to_attach"
        ):
            ep_client.blueprints[blueprint_id].endpoint_policies[pol["id"]].patch(
                {"attributes": {"rp_to_attach": pol["attributes"]["rp_to_attach"]}}
            )


# ── Main module logic ─────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
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
        # Instantiate the client factory and endpoint policy client
        client_factory = ApstraClientFactory.from_params(module)
        ep_client = client_factory.get_endpointpolicy_client()

        # Extract params from id / body
        id_param = module.params["id"] or {}
        body = module.params.get("body") or {}
        state = module.params["state"]

        blueprint_id = id_param.get("blueprint")
        if not blueprint_id:
            raise ValueError("'id.blueprint' is required")
        ct_id = id_param.get("ct_id")
        name = body.get("name")
        ct_type = body.get("type")
        description = body.get("description", "") or ""
        tags = body.get("tags") or []
        primitives = body.get("primitives")

        # ── Lookup existing CT ────────────────────────────────────────
        current_parsed = None
        if ct_id:
            # Direct lookup by ID via export
            try:
                current_parsed = _export_ct(ep_client, blueprint_id, ct_id)
            except Exception:
                current_parsed = None
        elif name:
            ct_id, current_parsed = _find_ct_by_name(ep_client, blueprint_id, name)

        # ── STATE: present ────────────────────────────────────────────
        if state == "present":
            if primitives is None:
                raise ValueError("'primitives' is required when state is 'present'")
            if not name and not ct_id:
                raise ValueError("Either 'name' or 'ct_id' is required")
            if not ct_type:
                raise ValueError("'type' is required when state is 'present'")

            # Validate primitives against CT type rules
            try:
                validate_primitives(ct_type, primitives)
            except CTValidationError as e:
                raise ValueError(str(e))

            ct_name = name or (
                current_parsed.get("name") if current_parsed else "unnamed"
            )

            if current_parsed:
                # ── Update path: compare current vs desired ───────────
                current_norm = normalize_for_compare(
                    current_parsed.get("primitives", {})
                )
                desired_norm = normalize_for_compare(primitives)

                desc_changed = description != current_parsed.get("description", "")
                tags_changed = sorted(tags) != sorted(current_parsed.get("tags", []))
                prims_changed = current_norm != desired_norm

                if prims_changed or desc_changed or tags_changed:
                    # Save existing assignments before deleting
                    saved_app_points = _get_ct_assignments(
                        ep_client, blueprint_id, ct_id
                    )
                    if saved_app_points:
                        _unassign_ct(ep_client, blueprint_id, ct_id, saved_app_points)

                    # Delete old CT and recreate (atomic replace)
                    ep_client.blueprints[blueprint_id].endpoint_policies[ct_id].delete()

                    payload, hierarchy = build_ct_payload(
                        ct_name, primitives, description, tags
                    )
                    ep_client.blueprints[blueprint_id].obj_policy_import.put(payload)
                    _refresh_rp_bindings(ep_client, blueprint_id, hierarchy)

                    ct_id = get_ct_id_from_hierarchy(hierarchy)

                    # Restore assignments to the new CT
                    if saved_app_points:
                        _reassign_ct(ep_client, blueprint_id, ct_id, saved_app_points)

                    result["changed"] = True
                    result["msg"] = "connectivity_template updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = (
                        "connectivity_template already exists, " "no changes needed"
                    )
            else:
                # ── Create path ───────────────────────────────────────
                payload, hierarchy = build_ct_payload(
                    ct_name, primitives, description, tags
                )
                ep_client.blueprints[blueprint_id].obj_policy_import.put(payload)
                _refresh_rp_bindings(ep_client, blueprint_id, hierarchy)

                ct_id = get_ct_id_from_hierarchy(hierarchy)
                result["changed"] = True
                result["msg"] = "connectivity_template created successfully"

            # Return final state
            result["ct_id"] = ct_id
            if ct_id:
                # Fetch the final export with retry
                final_parsed = None
                for _attempt in range(5):
                    try:
                        final_parsed = _export_ct(ep_client, blueprint_id, ct_id)
                        if final_parsed:
                            break
                    except Exception:
                        pass
                    time.sleep(1)

                if final_parsed:
                    result["connectivity_template"] = final_parsed
                else:
                    result["connectivity_template"] = {
                        "name": ct_name,
                        "ct_id": ct_id,
                    }

        # ── STATE: absent ─────────────────────────────────────────────
        elif state == "absent":
            if not ct_id and name:
                ct_id, _ = _find_ct_by_name(ep_client, blueprint_id, name)

            if ct_id:
                # Unassign from all application points before deleting
                saved_app_points = _get_ct_assignments(ep_client, blueprint_id, ct_id)
                if saved_app_points:
                    _unassign_ct(ep_client, blueprint_id, ct_id, saved_app_points)

                ep_client.blueprints[blueprint_id].endpoint_policies[ct_id].delete()
                result["changed"] = True
                result["msg"] = "connectivity_template deleted successfully"
            else:
                result["changed"] = False
                result["msg"] = "connectivity_template not found, nothing to delete"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
