#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: interconnect_gateway

short_description: Manage EVPN Interconnect Domains and their Gateways in Apstra blueprints

version_added: "0.2.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module manages both EVPN Interconnect Domains and
    Interconnect Domain Gateways within an Apstra blueprint.
  - Use C(type=domain) to manage Interconnect Domains (EVPN
    Interconnect Groups) that group sites for EVPN-based DCI.
  - Use C(type=gateway) (the default) to manage Interconnect Domain
    Gateways — remote EVPN gateways linked to an Interconnect Domain.
  - The equivalent Terraform resources are
    C(apstra_datacenter_interconnect_domain) and
    C(apstra_datacenter_interconnect_domain_gateway).

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
  type:
    description:
      - The type of interconnect resource to manage.
      - C(domain) manages Interconnect Domains (EVPN Interconnect
        Groups). Body fields are C(label), C(route_target), and
        optional C(esi_mac).
      - C(gateway) manages Interconnect Domain Gateways (remote
        gateways linked to a domain). Body fields are C(gw_name),
        C(gw_ip), C(gw_asn), C(local_gw_nodes), and
        C(evpn_interconnect_group_id).
    required: false
    type: str
    choices: ["domain", "gateway"]
    default: "gateway"
  id:
    description:
      - Dictionary containing the blueprint and resource IDs.
      - C(blueprint) is always required.
      - "For C(type=domain): C(evpn_interconnect_group) is optional
        for create (looked up by C(label) for idempotency), required
        for update/delete."
      - "For C(type=gateway): C(remote_gateway) is optional for
        create (looked up by C(gw_name) for idempotency), required
        for update/delete."
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the resource details.
      - "For C(type=domain):"
      - "  C(label) (string) - Domain name (required for create)."
      - "  C(route_target) (string) - Interconnect Route Target in
        C(<asn>:<nn>) format (required for create)."
      - "  C(esi_mac) (string) - Optional per-site ESI MAC address."
      - "  C(security_zones) (dict) - DCI Layer-3 (Type-5) settings
        keyed by VRF label or ID (auto-resolved). Each value is a
        dict with C(routing_policy_id) (label or ID, auto-resolved),
        C(interconnect_route_target) (string), and C(enabled_for_l3)
        (bool). Optional."
      - "  C(virtual_networks) (dict) - VN connection type settings
        keyed by virtual network label or ID (auto-resolved). Each
        value is a dict with C(l2) (bool), C(l3) (bool), and
        C(translation_vni) (integer). Optional."
      - "For C(type=gateway):"
      - "  C(gw_name) (string) - Gateway name (required for create)."
      - "  C(gw_ip) (string) - Gateway IPv4 address (required for
        create)."
      - "  C(gw_asn) (integer) - Gateway AS number, 1-4294967295
        (required for create)."
      - "  C(local_gw_nodes) (list) - IDs or labels of leaf switches
        that peer with this gateway (required for create)."
      - "  C(evpn_interconnect_group_id) (string) - ID of the parent
        Interconnect Domain (required for create)."
      - "  C(ttl) (integer) - BGP TTL in hops (optional)."
      - "  C(keepalive_timer) (integer) - BGP keepalive in seconds
        (optional)."
      - "  C(holdtime_timer) (integer) - BGP hold time in seconds
        (optional)."
      - "  C(password) (string) - BGP session password (optional)."
    required: false
    type: dict
  state:
    description:
      - Desired state of the resource.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ---- Interconnect Domain (type: domain) ----

# Create an Interconnect Domain (blueprint may be name or UUID)
- name: Create interconnect domain
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "my-datacenter-blueprint"
    body:
      label: "dci-domain-1"
      route_target: "65500:100"
    state: present
  register: icd

# Create domain with ESI MAC
- name: Create interconnect domain with ESI MAC
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "dci-domain-2"
      route_target: "65500:200"
      esi_mac: "02:00:00:00:00:01"
    state: present
  register: icd_2

# Update a domain by providing its ID
- name: Update interconnect domain route_target by ID
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      evpn_interconnect_group: "{{ icd.id.evpn_interconnect_group }}"
    body:
      label: "dci-domain-1"
      route_target: "65500:101"
    state: present

# Update a domain by label (no ID needed — looked up automatically)
- name: Update interconnect domain by label
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "dci-domain-1"
      route_target: "65500:102"
    state: present

# Delete a domain by explicit ID
- name: Delete interconnect domain by ID
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      evpn_interconnect_group: "{{ icd.id.evpn_interconnect_group }}"
    state: absent

# Delete a domain by label (no evpn_interconnect_group ID needed)
- name: Delete interconnect domain by label
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "dci-domain-2"
    state: absent

# ---- DCI Layer-3 (Type-5) via security_zones ----

# Enable L3 DCI on a VRF with a routing policy and route target.
# VRF labels and routing policy labels are resolved automatically.
- name: Enable L3 DCI on interconnect domain
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "my-datacenter-blueprint"
    body:
      label: "dci-domain-1"
      route_target: "65500:100"
      security_zones:
        "my-vrf":
          routing_policy_id: "dci-l3-policy"
          interconnect_route_target: "65500:200"
          enabled_for_l3: true
    state: present

# ---- VN Connection Type via virtual_networks ----

# Set L2+L3 connection type and translation VNI for a virtual network.
# VN labels are resolved automatically.
- name: Set VN connection type with translation VNI
  juniper.apstra.interconnect_gateway:
    type: domain
    id:
      blueprint: "my-datacenter-blueprint"
    body:
      label: "dci-domain-1"
      route_target: "65500:100"
      virtual_networks:
        "my-virtual-network":
          l2: true
          l3: true
          translation_vni: 10100
    state: present

# ---- Interconnect Domain Gateway (type: gateway) ----

# Create a gateway — local_gw_nodes accepts system labels OR raw node IDs.
# evpn_interconnect_group_id accepts the domain label OR its UUID.
- name: Create interconnect gateway using system labels and domain label
  juniper.apstra.interconnect_gateway:
    id:
      blueprint: "my-datacenter-blueprint"
    body:
      gw_name: "remote-dc2-gw"
      gw_ip: "10.1.0.1"
      gw_asn: 65500
      evpn_interconnect_group_id: "dci-domain-1"
      local_gw_nodes:
        - "border-leaf-1"
        - "border-leaf-2"
      ttl: 2
      keepalive_timer: 10
      holdtime_timer: 30
    state: present
  register: icgw

# Create a gateway using raw node IDs and domain UUID
- name: Create interconnect gateway using raw IDs
  juniper.apstra.interconnect_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      gw_name: "remote-dc2-gw"
      gw_ip: "10.1.0.1"
      gw_asn: 65500
      evpn_interconnect_group_id: "{{ icd.id.evpn_interconnect_group }}"
      local_gw_nodes:
        - "PPbnMs25oIuO8WHldA"
        - "QCbnMs25oIuO8WHldB"
      ttl: 2
    state: present
  register: icgw

# Update a gateway by providing its ID
- name: Update interconnect gateway by ID
  juniper.apstra.interconnect_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      remote_gateway: "{{ icgw.id.remote_gateway }}"
    body:
      gw_name: "remote-dc2-gw"
      gw_ip: "10.1.0.2"
      gw_asn: 65500
      evpn_interconnect_group_id: "{{ icd.id.evpn_interconnect_group }}"
      local_gw_nodes:
        - "border-leaf-1"
    state: present

# Update a gateway by name lookup (no remote_gateway ID needed)
- name: Update interconnect gateway by gw_name
  juniper.apstra.interconnect_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      gw_name: "remote-dc2-gw"
      gw_ip: "10.1.0.3"
      gw_asn: 65500
      evpn_interconnect_group_id: "dci-domain-1"
      local_gw_nodes:
        - "border-leaf-1"
    state: present

# Delete an interconnect gateway by ID
- name: Delete interconnect gateway
  juniper.apstra.interconnect_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      remote_gateway: "{{ icgw.id.remote_gateway }}"
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
changes:
  description: Dictionary of updates that were applied.
  type: dict
  returned: on update
response:
  description: The resource object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: >
    The ID dictionary.  For type=domain contains C(blueprint) and
    C(evpn_interconnect_group).  For type=gateway contains
    C(blueprint) and C(remote_gateway).
  returned: on create, or when object identified by label/gw_name
  type: dict
evpn_interconnect_group:
  description: The interconnect domain object (type=domain).
  type: dict
  returned: when type=domain and state=present
remote_gateway:
  description: The interconnect gateway object (type=gateway).
  type: dict
  returned: when type=gateway and state=present
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
    singular_leaf_object_type,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_interconnect_domain_id,
    resolve_system_node_id,
    resolve_virtual_network_id,
    resolve_security_zone_id,
    resolve_routing_policy_id,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_dci import (
    patch_interconnect_domain_raw,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interconnect_domain import (
    get_interconnect_domain,
    create_interconnect_domain,
    update_interconnect_domain,
    delete_interconnect_domain,
    find_interconnect_domain_by_label,
)


# ──────────────────────────────────────────────────────────────────
#  Gateway helpers
# ──────────────────────────────────────────────────────────────────


def _find_interconnect_gateway_by_name(client_factory, object_type, id, gw_name):
    """
    Search for an existing interconnect gateway by gw_name.

    Only returns gateways that have evpn_interconnect_group_id set.
    """
    all_gateways = client_factory.object_request(object_type, "get", id)
    if isinstance(all_gateways, list):
        items = all_gateways
    elif isinstance(all_gateways, dict):
        items = all_gateways.get("remote_gateways", list(all_gateways.values()))
    else:
        return None

    for gw in items:
        if (
            isinstance(gw, dict)
            and gw.get("gw_name") == gw_name
            and gw.get("evpn_interconnect_group_id")
        ):
            return gw
    return None


# ──────────────────────────────────────────────────────────────────
#  DCI raw-PATCH builder
# ──────────────────────────────────────────────────────────────────


def _build_dci_patch(client_factory, blueprint_id, raw_fields):
    """Build a raw PATCH payload for DCI-extension fields.

    Resolves labels → node IDs for security_zones and virtual_networks
    sub-keys, then returns the SDK-style payload for
    ``patch_interconnect_domain_raw``.
    """
    payload = {}

    # security_zones: { "<sz_label_or_id>": { routing_policy_id, ... } }
    if "security_zones" in raw_fields:
        resolved = {}
        for sz_key, sz_cfg in raw_fields["security_zones"].items():
            sz_id = resolve_security_zone_id(client_factory, blueprint_id, sz_key)
            entry = dict(sz_cfg) if isinstance(sz_cfg, dict) else {}
            # Resolve routing_policy_id label → ID
            if "routing_policy_id" in entry:
                entry["routing_policy_id"] = resolve_routing_policy_id(
                    client_factory, blueprint_id, entry["routing_policy_id"]
                )
            resolved[sz_id] = entry
        payload["interconnect_security_zones"] = resolved

    # virtual_networks: { "<vn_label_or_id>": { l2, l3, translation_vni } }
    if "virtual_networks" in raw_fields:
        resolved = {}
        for vn_key, vn_cfg in raw_fields["virtual_networks"].items():
            vn_id = resolve_virtual_network_id(client_factory, blueprint_id, vn_key)
            entry = dict(vn_cfg) if isinstance(vn_cfg, dict) else {}
            resolved[vn_id] = entry
        payload["interconnect_virtual_networks"] = resolved

    return payload


# ──────────────────────────────────────────────────────────────────
#  Domain logic
# ──────────────────────────────────────────────────────────────────


def _run_domain(module, client_factory, result):
    """Manage an Interconnect Domain (EVPN Interconnect Group)."""
    leaf_object_type = "evpn_interconnect_group"

    id = module.params["id"]
    body = module.params.get("body", None)
    state = module.params["state"]

    if "blueprint" not in id:
        raise ValueError("'blueprint' is required in id")
    id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])
    blueprint_id = id["blueprint"]

    domain_id = id.get(leaf_object_type, None)

    # Look up existing object
    current_object = None
    if domain_id is not None:
        current_object = get_interconnect_domain(
            client_factory, blueprint_id, domain_id
        )
    elif body is not None and "label" in body:
        found = find_interconnect_domain_by_label(
            client_factory, blueprint_id, body["label"]
        )
        if found:
            domain_id = found["id"]
            id[leaf_object_type] = domain_id
            current_object = found

    # Separate DCI-extension fields that require raw PATCH
    raw_patch_fields = {}
    if body:
        if "security_zones" in body:
            raw_patch_fields["security_zones"] = body.pop("security_zones")
        if "virtual_networks" in body:
            raw_patch_fields["virtual_networks"] = body.pop("virtual_networks")

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                # Map body keys to SDK-style keys for comparison
                compare_body = {}
                if "label" in body:
                    compare_body["label"] = body["label"]
                if "route_target" in body:
                    compare_body["interconnect_route_target"] = body["route_target"]
                if "esi_mac" in body:
                    compare_body["interconnect_esi_mac"] = body["esi_mac"]

                changes = {}
                if client_factory.compare_and_update(
                    dict(current_object), compare_body, changes
                ):
                    updated = update_interconnect_domain(
                        client_factory, blueprint_id, domain_id, body
                    )
                    result["changed"] = True
                    if updated:
                        result["response"] = updated
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = (
                        f"{leaf_object_type} already exists, no changes needed"
                    )
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None and not raw_patch_fields:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            if body is None:
                body = {}
            created = create_interconnect_domain(client_factory, blueprint_id, body)
            if isinstance(created, dict) and "id" in created:
                domain_id = created["id"]
                id[leaf_object_type] = domain_id
            result["id"] = id
            result["changed"] = True
            result["response"] = created
            result["msg"] = f"{leaf_object_type} created successfully"

        # Apply raw PATCH for DCI-extension fields (L3, VN)
        if raw_patch_fields and domain_id:
            patch_payload = _build_dci_patch(
                client_factory, blueprint_id, raw_patch_fields
            )
            if patch_payload:
                # Compare against current state to avoid no-op PATCHes.
                # The current object may contain extra read-only fields
                # (routing_policy_label, security_zone_id, vrf_name, …)
                # so we only check the fields we intend to set.
                cur = (
                    get_interconnect_domain(client_factory, blueprint_id, domain_id)
                    or {}
                )
                needs_patch = False
                for k, desired in patch_payload.items():
                    current = cur.get(k, {})
                    if isinstance(desired, dict) and isinstance(current, dict):
                        for sub_key, sub_desired in desired.items():
                            sub_current = current.get(sub_key, {})
                            if isinstance(sub_desired, dict) and isinstance(
                                sub_current, dict
                            ):
                                for field, val in sub_desired.items():
                                    if sub_current.get(field) != val:
                                        needs_patch = True
                                        break
                                if needs_patch:
                                    break
                            elif sub_current != sub_desired:
                                needs_patch = True
                                break
                        if needs_patch:
                            break
                    elif current != desired:
                        needs_patch = True
                        break
                if needs_patch:
                    patch_interconnect_domain_raw(
                        client_factory, blueprint_id, domain_id, patch_payload
                    )
                    result["changed"] = True
                    result.setdefault("changes", {})
                    result["changes"].update(patch_payload)
                    result["msg"] = f"{leaf_object_type} updated successfully"

        # Return the final object state
        final_obj = get_interconnect_domain(client_factory, blueprint_id, domain_id)
        if final_obj:
            result[leaf_object_type] = final_obj

    elif state == "absent":
        # Allow delete by label: look up domain_id from body.label when
        # id.evpn_interconnect_group is not provided.
        if domain_id is None:
            if body is not None and "label" in body:
                found = find_interconnect_domain_by_label(
                    client_factory, blueprint_id, body["label"]
                )
                if found:
                    domain_id = found["id"]
                    id[leaf_object_type] = domain_id
            if domain_id is None:
                raise ValueError(
                    f"Must specify '{leaf_object_type}' in id or 'label' in body to delete"
                )
        delete_interconnect_domain(client_factory, blueprint_id, domain_id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


# ──────────────────────────────────────────────────────────────────
#  Gateway logic
# ──────────────────────────────────────────────────────────────────


def _run_gateway(module, client_factory, result):
    """Manage an Interconnect Domain Gateway (remote gateway)."""
    object_type = "blueprints.remote_gateways"
    leaf_object_type = singular_leaf_object_type(object_type)

    id = module.params["id"]
    body = module.params.get("body", None)
    state = module.params["state"]

    if "blueprint" not in id:
        raise ValueError("'blueprint' is required in id")
    id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])
    bp_id = id["blueprint"]

    # Coerce integer fields
    _INT_FIELDS = ("gw_asn", "ttl", "keepalive_timer", "holdtime_timer")
    if body:
        for field in _INT_FIELDS:
            if field in body and body[field] is not None:
                try:
                    body[field] = int(body[field])
                except (ValueError, TypeError):
                    raise ValueError(
                        f"'{field}' must be an integer, got: {body[field]!r}"
                    )

        # Resolve local_gw_nodes system labels to graph node UUIDs
        if "local_gw_nodes" in body and isinstance(body["local_gw_nodes"], list):
            body["local_gw_nodes"] = [
                resolve_system_node_id(client_factory, bp_id, node)
                for node in body["local_gw_nodes"]
            ]

        # Resolve evpn_interconnect_group_id from label to ID
        if "evpn_interconnect_group_id" in body and body["evpn_interconnect_group_id"]:
            body["evpn_interconnect_group_id"] = resolve_interconnect_domain_id(
                client_factory, bp_id, body["evpn_interconnect_group_id"]
            )

        # Validate evpn_interconnect_group_id on create
        if state == "present" and "evpn_interconnect_group_id" not in body:
            if leaf_object_type not in id:
                raise ValueError(
                    "'evpn_interconnect_group_id' is required in body "
                    "when creating an interconnect gateway"
                )

    # Validate the id
    missing_id = client_factory.validate_id(object_type, id)
    if len(missing_id) > 1 or (
        len(missing_id) == 1 and state == "absent" and missing_id[0] != leaf_object_type
    ):
        raise ValueError(f"Invalid id: {id} for desired state of {state}.")
    object_id = id.get(leaf_object_type, None)

    # Look up existing object
    current_object = None
    if object_id is None:
        if body is not None and "gw_name" in body:
            found = _find_interconnect_gateway_by_name(
                client_factory, object_type, id, body["gw_name"]
            )
            if found:
                id[leaf_object_type] = found["id"]
                current_object = found
    else:
        current_object = client_factory.object_request(object_type, "get", id)
        if isinstance(current_object, list) and len(current_object) > 0:
            current_object = current_object[0]

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                # Normalize local_gw_nodes for comparison
                compare_object = dict(current_object)
                if "local_gw_nodes" in compare_object and isinstance(
                    compare_object["local_gw_nodes"], list
                ):
                    normalized = []
                    for node in compare_object["local_gw_nodes"]:
                        if isinstance(node, dict) and "node_id" in node:
                            normalized.append(node["node_id"])
                        else:
                            normalized.append(node)
                    compare_object["local_gw_nodes"] = sorted(normalized)

                compare_body = dict(body)
                if "local_gw_nodes" in compare_body and isinstance(
                    compare_body["local_gw_nodes"], list
                ):
                    compare_body["local_gw_nodes"] = sorted(
                        compare_body["local_gw_nodes"]
                    )

                changes = {}
                if client_factory.compare_and_update(
                    compare_object, compare_body, changes
                ):
                    updated_object = client_factory.object_request(
                        object_type, "update", id, body
                    )
                    result["changed"] = True
                    if updated_object:
                        result["response"] = updated_object
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = (
                        f"{leaf_object_type} already exists, no changes needed"
                    )
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            created = client_factory.object_request(object_type, "create", id, body)
            if isinstance(created, dict) and "id" in created:
                object_id = created["id"]
                id[leaf_object_type] = object_id
            result["id"] = id
            result["changed"] = True
            result["response"] = created
            result["msg"] = f"{leaf_object_type} created successfully"

        # Return the final object state
        if current_object is not None:
            result[leaf_object_type] = current_object
        elif id.get(leaf_object_type):
            final_obj = client_factory.object_request(
                object_type=object_type,
                op="get",
                id=id,
                retry=10,
                retry_delay=3,
            )
            if isinstance(final_obj, list) and len(final_obj) > 0:
                final_obj = final_obj[0]
            result[leaf_object_type] = final_obj

    if id is None:
        raise ValueError(f"Cannot manage a {leaf_object_type} without an object id")

    if state == "absent":
        if leaf_object_type not in id:
            raise ValueError(f"Must specify '{leaf_object_type}' in id to delete")
        client_factory.object_request(object_type, "delete", id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


# ──────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        type=dict(
            type="str",
            required=False,
            choices=["domain", "gateway"],
            default="gateway",
        ),
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
        client_factory = ApstraClientFactory.from_params(module)
        resource_type = module.params["type"]

        if resource_type == "domain":
            _run_domain(module, client_factory, result)
        else:
            _run_gateway(module, client_factory, result)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
