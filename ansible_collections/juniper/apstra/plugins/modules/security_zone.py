#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: security_zone

short_description: Manage security zones (tenants/VRFs) and tenants in Apstra

version_added: "1.0.9"

author:
  - "Edwin Jacques (@edwinpjacques)"

description:
  - This module allows you to create, update, and delete security zones in Apstra.
  - Security zones map to VRFs/tenants in Apstra.
  - Supports tenant-centric parameter aliases for intuitive VRF management.
  - Supports bulk tenant operations via the C(tenants) parameter.
  - Supports managing actual Tenant objects (grouping of routing zones)
    via the C(tenant) parameter.

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
      - Dictionary containing the blueprint and security zone IDs.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the security zone object details.
      - Tenant-centric aliases are supported and mapped to their
        security zone equivalents (e.g. C(tenant_label) -> C(label),
        C(tenant_description) -> C(vrf_description)).
    required: false
    type: dict
  tags:
    description:
      - List of tags to apply to the security zone.
    type: list
    elements: str
  tenant:
    description:
      - A single tenant definition for managing an Apstra Tenant object.
      - A Tenant groups routing zones (security zones) under a label.
      - Required keys C(label) and optional C(routing_zones) (list of
        security zone IDs or labels to assign).
      - Mutually exclusive with C(body) and C(tenants).
    type: dict
    required: false
  tenants:
    description:
      - List of tenant definitions for bulk operations.
      - Each entry is a dict with C(label) and optional C(routing_zones).
      - A per-tenant C(state) key (present/absent) can override the
        top-level C(state).
      - Mutually exclusive with C(body) and C(tenant).
    type: list
    elements: dict
    required: false
  state:
    description:
      - Desired state of the security zone or tenant.
      - Use C(list) to enumerate all security zones and tenants in the blueprint.
    required: false
    type: str
    choices: ["present", "absent", "list"]
    default: "present"
"""

EXAMPLES = """
- name: Create a security zone
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      description: "Example security zone"
      expect_default_ipv4_route: true
      expect_default_ipv6_route: true
      export_policy:
        l2edge_subnets: true
        loopbacks: true
        spine_leaf_links: false
        spine_superspine_links: false
        static_routes: false
      import_policy: "all"
      label: "example_policy"
      policy_type: "user_defined"
    state: present

- name: Create a tenant using tenant-centric aliases
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      tenant_label: "web-tier"
      tenant_description: "Web tier VRF"
      vni_id: 10001
      sz_type: "evpn"
    state: present

- name: Update a security zone (or update it if the label exists)
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      security_zone: "AjAuUuVLylXCUgAqaQ"
    body:
      description: "example security zone UPDATE"
      import_policy: "extra_only"
    state: present

- name: Delete a security zone
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      security_zone: "AjAuUuVLylXCUgAqaQ"
    state: absent

- name: List all security zones / tenants in a blueprint
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    state: list

- name: Bulk create/update tenants
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    tenants:
      - label: "production"
        routing_zones:
          - "web-tier"
          - "app-tier"
      - label: "staging"
        routing_zones:
          - "db-tier"
      - label: "old-tenant"
        state: absent
    state: present

- name: Create a single tenant with routing zones
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    tenant:
      label: "production"
      routing_zones:
        - "web-tier"
        - "app-tier"
    state: present

- name: Delete a tenant
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    tenant:
      label: "production"
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
  description: The security zone object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the created security zone.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "security_zone": "AjAuUuVLylXCUgAqaQ"
  }
security_zone:
  description: The security zone object details.
  returned: on create or update
  type: dict
  sample: {
      "id": "AjAuUuVLylXCUgAqaQ",
      "label": "example_policy",
      "description": "example security zone",
      "expect_default_ipv4_route": true,
      "expect_default_ipv6_route": true,
      "export_policy": {
          "l2edge_subnets": true,
          "loopbacks": true,
          "spine_leaf_links": false,
          "spine_superspine_links": false,
          "static_routes": false
      },
      "import_policy": "all",
      "policy_type": "user_defined"
  }
security_zones:
  description: List of all security zones in the blueprint.
  returned: when state is list
  type: list
tag_response:
  description: The response from applying tags to the security zone.
  type: list
  returned: when tags are applied
  sample: ["red", "blue"]
tenants:
  description: Results of bulk tenant operations or list of all tenants.
  returned: when tenants/tenant parameter is used, or state is list
  type: list
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
    resolve_security_zone_id,
    resolve_vrf_interface_pair,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_nodes import (
    get_node,
    patch_node,
    node_needs_update,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_tenants import (
    list_tenants,
    create_tenant,
    update_tenant,
    delete_tenant,
    find_tenant_by_label,
    resolve_security_zone_ids,
)

# Tenant-centric alias mapping: tenant param → security zone param
TENANT_ALIASES = {
    "tenant_label": "label",
    "tenant_description": "vrf_description",
}


def _resolve_tenant_aliases(body):
    """Translate tenant-centric parameter aliases to their SZ equivalents.

    If both the alias and the canonical key are present, the canonical
    key takes precedence and the alias is silently dropped.
    """
    if not body:
        return body
    for alias, canonical in TENANT_ALIASES.items():
        if alias in body:
            # Canonical key already present — drop the alias
            if canonical not in body:
                body[canonical] = body[alias]
            del body[alias]
    return body


def _manage_single_security_zone(
    client_factory, module, object_type, leaf_object_type, id, body, state, tags
):
    """Create, update, or delete a single security zone.

    Returns a per-item result dict with keys: changed, id, msg, and
    optionally response, changes, tag_response, security_zone, ip_assignments.
    """
    result = dict(changed=False)

    # Resolve tenant aliases
    body = _resolve_tenant_aliases(body)

    # Pop custom fields that the Apstra API does not understand
    interfaces_ip_assignments = None
    sz_name = None
    if body:
        interfaces_ip_assignments = body.pop("interfaces_ip_assignments", None)
        sz_name = body.pop("sz_name", None)
        # Pop tags from body and merge with top-level tags parameter
        body_tags = body.pop("tags", None)
        if body_tags is not None:
            if tags is not None:
                tags = list(set(tags) | set(body_tags))
            else:
                tags = body_tags
        if sz_name:
            body.setdefault("label", sz_name)
            if set(body.keys()) == {"label"}:
                body = None
        elif not body:
            body = None

    # Resolve security_zone name/label to ID if needed
    if leaf_object_type in id and id[leaf_object_type]:
        id[leaf_object_type] = resolve_security_zone_id(
            client_factory,
            id["blueprint"],
            id[leaf_object_type],
            raise_on_missing=True,
        )

    # Coerce integer fields that the API requires as int, not str
    if body:
        for int_field in ("vni_id", "vlan_id"):
            if int_field in body and body[int_field] is not None:
                body[int_field] = int(body[int_field])

    # Validate the id
    missing_id = client_factory.validate_id(object_type, id)
    if len(missing_id) > 1 or (
        len(missing_id) == 1 and state == "absent" and missing_id[0] != leaf_object_type
    ):
        raise ValueError(f"Invalid id: {id} for desired state of {state}.")
    object_id = id.get(leaf_object_type, None)

    # See if the object exists
    current_object = None
    lookup_label = (body or {}).get("label") or sz_name
    if object_id is None:
        if lookup_label:
            id_found = resolve_security_zone_id(
                client_factory,
                id["blueprint"],
                lookup_label,
                raise_on_missing=(body is None),
            )
        else:
            id_found = None

        if id_found:
            id[leaf_object_type] = id_found
            current_object = client_factory.object_request(object_type, "get", id)
    else:
        current_object = client_factory.object_request(object_type, "get", id)

    # Make the requested changes
    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                changes = {}
                if client_factory.compare_and_update(current_object, body, changes):
                    updated_object = client_factory.object_request(
                        object_type, "patch", id, changes
                    )
                    result["changed"] = True
                    if updated_object:
                        result["response"] = updated_object
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            obj = client_factory.object_request(object_type, "create", id, body)
            object_id = obj["id"]
            id[leaf_object_type] = object_id
            result["id"] = id
            result["changed"] = True
            result["response"] = obj
            result["msg"] = f"{leaf_object_type} created successfully"

        # Apply tags if specified
        if tags is not None:
            result["tag_response"] = client_factory.update_tags(
                id, leaf_object_type, tags
            )

        # Return the final object state
        if current_object is not None:
            result[leaf_object_type] = current_object
        else:
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type, op="get", id=id, retry=10, retry_delay=3
            )

        # Apply interface IP assignments if specified
        if interfaces_ip_assignments:
            _apply_interface_ip_assignments(
                client_factory,
                id["blueprint"],
                id[leaf_object_type],
                interfaces_ip_assignments,
                result,
            )

    if state == "absent":
        if current_object:
            client_factory.object_request(object_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{leaf_object_type} deleted successfully"
        else:
            result["changed"] = False
            result["msg"] = f"{leaf_object_type} not found, nothing to delete"

    return result


def _apply_interface_ip_assignments(
    client_factory, blueprint_id, sz_id, assignments, result
):
    """Patch IP addresses on VRF interface endpoints.

    For each entry in *assignments*, resolves the interface within the
    security zone, then patches endpoint1 and (optionally) endpoint2
    with the specified IPv4 address / type.

    :param assignments: List of dicts, each with ``interface``,
        ``endpoint1_ipv4_address``, etc.
    :param result: Module result dict — ``changed`` and
        ``ip_assignments`` are updated in-place.
    """
    ip_results = []
    for assignment in assignments:
        interface_name = assignment["interface"]
        ep1_id, ep2_id = resolve_vrf_interface_pair(
            client_factory, blueprint_id, sz_id, interface_name
        )

        entry = {"interface": interface_name, "endpoint1_id": ep1_id}

        # ── Patch endpoint1 ──────────────────────────────────────
        if "endpoint1_ipv4_address" in assignment:
            ep1_props = {"ipv4_addr": assignment["endpoint1_ipv4_address"]}
            if "endpoint1_ipv4_type" in assignment:
                ep1_props["ipv4_type"] = assignment["endpoint1_ipv4_type"]
            current = get_node(client_factory, blueprint_id, ep1_id)
            changes = node_needs_update(current, ep1_props)
            if changes:
                patch_node(client_factory, blueprint_id, ep1_id, changes)
                result["changed"] = True
                entry["endpoint1_changed"] = True

        # ── Patch endpoint2 ──────────────────────────────────────
        if ep2_id and "endpoint2_ipv4_address" in assignment:
            ep2_props = {"ipv4_addr": assignment["endpoint2_ipv4_address"]}
            if "endpoint2_ipv4_type" in assignment:
                ep2_props["ipv4_type"] = assignment["endpoint2_ipv4_type"]
            current = get_node(client_factory, blueprint_id, ep2_id)
            changes = node_needs_update(current, ep2_props)
            if changes:
                patch_node(client_factory, blueprint_id, ep2_id, changes)
                result["changed"] = True
                entry["endpoint2_changed"] = True
            entry["endpoint2_id"] = ep2_id
        elif "endpoint2_ipv4_address" in assignment and not ep2_id:
            entry["endpoint2_warning"] = "No link partner found"

        ip_results.append(entry)

    result["ip_assignments"] = ip_results


def _manage_single_tenant(client_factory, blueprint_id, tenant_def, state):
    """Create, update, or delete a single Apstra Tenant object.

    A Tenant groups routing zones (security zones) under a label.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        tenant_def: Dict with ``label`` and optional ``routing_zones``.
        state: ``"present"`` or ``"absent"``.

    Returns:
        dict: Per-item result with ``changed``, ``msg``, etc.
    """
    result = dict(changed=False)
    label = tenant_def.get("label")
    if not label:
        raise ValueError("Each tenant must have a 'label'")

    routing_zone_refs = tenant_def.get("routing_zones", [])

    # Resolve routing zone labels/IDs
    sz_ids = []
    if routing_zone_refs:
        sz_ids = resolve_security_zone_ids(
            client_factory, blueprint_id, routing_zone_refs
        )

    # Check if tenant already exists
    existing = find_tenant_by_label(client_factory, blueprint_id, label)

    if state == "present":
        if existing:
            tenant_id = existing["id"]
            current_sz_ids = sorted(existing.get("application_node_ids", []))
            desired_sz_ids = sorted(sz_ids)
            if current_sz_ids != desired_sz_ids and routing_zone_refs:
                update_tenant(client_factory, blueprint_id, tenant_id, sz_ids)
                result["changed"] = True
                result["msg"] = f"Tenant '{label}' updated"
                result["changes"] = {
                    "application_node_ids": {
                        "old": current_sz_ids,
                        "new": desired_sz_ids,
                    }
                }
                # Return expected state (API may be eventually consistent)
                result["tenant"] = {
                    "id": tenant_id,
                    "label": label,
                    "application_node_ids": desired_sz_ids,
                    "lowercased": label.lower(),
                }
            else:
                result["msg"] = f"Tenant '{label}' already exists, no changes"
                result["tenant"] = existing
            result["id"] = tenant_id
        else:
            obj = create_tenant(client_factory, blueprint_id, label, sz_ids)
            result["changed"] = True
            result["id"] = obj["id"]
            result["msg"] = f"Tenant '{label}' created"
            result["tenant"] = {
                "id": obj["id"],
                "label": label,
                "application_node_ids": sorted(sz_ids),
                "lowercased": label.lower(),
            }
    elif state == "absent":
        if existing:
            delete_tenant(client_factory, blueprint_id, existing["id"])
            result["changed"] = True
            result["msg"] = f"Tenant '{label}' deleted"
        else:
            result["msg"] = f"Tenant '{label}' not found, nothing to delete"

    return result


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent", "list"],
            default="present",
        ),
        tags=dict(type="list", elements="str", required=False),
        tenant=dict(type="dict", required=False),
        tenants=dict(type="list", elements="dict", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[
            ("body", "tenants"),
            ("body", "tenant"),
            ("tenant", "tenants"),
        ],
    )

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        object_type = "blueprints.security_zones"
        leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]
        tags = module.params.get("tags", None)
        tenant = module.params.get("tenant", None)
        tenants = module.params.get("tenants", None)

        # Resolve tenant aliases on the single-body path
        body = _resolve_tenant_aliases(body)

        # Resolve blueprint name to ID if needed
        if "blueprint" in id:
            id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])

        # ── state=list: enumerate all security zones and tenants ─
        if state == "list":
            all_sz = client_factory.object_request(object_type, "get", id)
            sz_list = []
            if isinstance(all_sz, dict):
                if "items" in all_sz:
                    sz_list = all_sz["items"]
                else:
                    sz_list = list(all_sz.values())
            elif isinstance(all_sz, list):
                sz_list = all_sz
            result["security_zones"] = sz_list
            # Also list actual Tenant objects
            result["tenants"] = list_tenants(client_factory, id["blueprint"])
            result["msg"] = (
                f"Found {len(sz_list)} security zone(s) and "
                f"{len(result['tenants'])} tenant(s)"
            )
            module.exit_json(**result)
            return

        # ── Single tenant object management ──────────────────────
        if tenant:
            t_result = _manage_single_tenant(
                client_factory, id["blueprint"], dict(tenant), state
            )
            result.update(t_result)
            module.exit_json(**result)
            return

        # ── Bulk tenant object operations ────────────────────────
        if tenants:
            tenant_results = []
            for tenant_def in tenants:
                tenant_def = dict(tenant_def)  # copy to avoid mutating input
                t_state = tenant_def.pop("state", state)
                t_result = _manage_single_tenant(
                    client_factory, id["blueprint"], tenant_def, t_state
                )
                if t_result.get("changed"):
                    result["changed"] = True
                tenant_results.append(t_result)
            result["tenants"] = tenant_results
            result["msg"] = f"Processed {len(tenant_results)} tenant(s)"
            module.exit_json(**result)
            return

        # ── Single security zone operation (original path) ───────
        # Pop custom fields that the Apstra API does not understand
        interfaces_ip_assignments = None
        sz_name = None
        if body:
            interfaces_ip_assignments = body.pop("interfaces_ip_assignments", None)
            sz_name = body.pop("sz_name", None)
            # Pop tags from body and merge with top-level tags parameter
            # Tags must go through update_tags(), not the create/patch API
            body_tags = body.pop("tags", None)
            if body_tags is not None:
                if tags is not None:
                    # Merge: top-level tags take precedence, add any from body
                    tags = list(set(tags) | set(body_tags))
                else:
                    tags = body_tags
            if sz_name:
                body.setdefault("label", sz_name)
                # When sz_name is the only source of "label" and no other
                # creation/update fields were supplied, mark this as a
                # lookup-only operation so we don't accidentally try to
                # create a VRF with incomplete data.
                if set(body.keys()) == {"label"}:
                    body = None
            elif not body:
                body = None

        # Resolve security_zone name/label to ID if needed
        if leaf_object_type in id and id[leaf_object_type]:
            id[leaf_object_type] = resolve_security_zone_id(
                client_factory,
                id["blueprint"],
                id[leaf_object_type],
                raise_on_missing=True,
            )

        # Coerce integer fields that the API requires as int, not str
        if body:
            for int_field in ("vni_id", "vlan_id"):
                if int_field in body and body[int_field] is not None:
                    body[int_field] = int(body[int_field])

        # Validate the id
        missing_id = client_factory.validate_id(object_type, id)
        if len(missing_id) > 1 or (
            len(missing_id) == 1
            and state == "absent"
            and missing_id[0] != leaf_object_type
        ):
            raise ValueError(f"Invalid id: {id} for desired state of {state}.")
        object_id = id.get(leaf_object_type, None)

        # See if the object exists
        current_object = None
        lookup_label = (body or {}).get("label") or sz_name
        if object_id is None:
            if lookup_label:
                # All name resolution goes through resolve_security_zone_id
                # which checks: exact ID → label → case-insensitive label
                # → vrf_name → case-insensitive vrf_name.
                # When body is None (lookup-only via sz_name), raise if
                # not found; otherwise return None so creation can proceed.
                id_found = resolve_security_zone_id(
                    client_factory,
                    id["blueprint"],
                    lookup_label,
                    raise_on_missing=(body is None),
                )
            else:
                id_found = None

            if id_found:
                id[leaf_object_type] = id_found
                current_object = client_factory.object_request(object_type, "get", id)
        else:
            current_object = client_factory.object_request(object_type, "get", id)

        # Make the requested changes
        if state == "present":
            if current_object:
                result["id"] = id
                if body:
                    # Update the object
                    changes = {}
                    if client_factory.compare_and_update(current_object, body, changes):
                        updated_object = client_factory.object_request(
                            object_type, "patch", id, changes
                        )
                        result["changed"] = True
                        if updated_object:
                            result["response"] = updated_object
                        result["changes"] = changes
                        result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = f"No changes specified for {leaf_object_type}"
            else:
                if body is None:
                    raise ValueError(
                        f"Must specify 'body' to create a {leaf_object_type}"
                    )
                # Create the object
                object = client_factory.object_request(object_type, "create", id, body)
                object_id = object["id"]
                id[leaf_object_type] = object_id
                result["id"] = id
                result["changed"] = True
                result["response"] = object
                result["msg"] = f"{leaf_object_type} created successfully"

            # Apply tags if specified (tags=[] removes all tags)
            if tags is not None:
                result["tag_response"] = client_factory.update_tags(
                    id, leaf_object_type, tags
                )

            # Return the final object state (avoid re-reading after updates
            # because SDK may return stale cached data; for creates, fetch
            # the full server-populated object)
            if current_object is not None:
                result[leaf_object_type] = current_object
            else:
                result[leaf_object_type] = client_factory.object_request(
                    object_type=object_type, op="get", id=id, retry=10, retry_delay=3
                )

            # Apply interface IP assignments if specified
            if interfaces_ip_assignments:
                _apply_interface_ip_assignments(
                    client_factory,
                    id["blueprint"],
                    id[leaf_object_type],
                    interfaces_ip_assignments,
                    result,
                )

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(f"Cannot manage a {leaf_object_type} without a object id")

        if state == "absent":
            # Delete the security zone
            client_factory.object_request(object_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{leaf_object_type} deleted successfully"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
