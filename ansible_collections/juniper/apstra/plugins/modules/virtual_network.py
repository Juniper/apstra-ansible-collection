#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: virtual_network

short_description: Manage virtual networks in Apstra

version_added: "0.1.0"

author:
  - "Edwin Jacques (@edwinpjacques)"

description:
  - This module allows you to create, update, and delete virtual networks in Apstra.

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
      - Dictionary containing the blueprint and virtual network IDs.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the virtual network object details.
    required: false
    type: dict
  tags:
    description:
      - List of tags to apply to the virtual network.
    type: list
    elements: str
  state:
    description:
      - Desired state of the virtual network.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Create a virtual network (or update it if the label exists)
  juniper.apstra.virtual_network:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "Test-VN-label"
      description: "test VN description"
      ipv4_enabled: true
      virtual_gateway_ipv4_enabled: true
      vn_id: "16777214"
      vn_type: "vxlan"
    state: present

- name: Update a virtual network
  juniper.apstra.virtual_network:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      virtual_network: "AjAuUuVLylXCUgAqaQ"
    body:
      description: "test VN description UPDATE"
      ipv4_enabled: false
    state: present

# Use names instead of IDs — security zone and bound_to system labels resolve automatically
- name: Create virtual network using names
  juniper.apstra.virtual_network:
    id:
      blueprint: "my-blueprint"
    body:
      label: "Test-VN-by-name"
      vn_type: "vxlan"
      security_zone_id: "my-routing-zone"
      bound_to:
        - system_id: "spine1"
          vlan_id: 100
    state: present

- name: Create virtual network with static IPv4
  juniper.apstra.virtual_network:
    id:
      blueprint: "my-blueprint"
    body:
      label: "Test-VN-static-IPv4"
      vn_type: "vxlan"
      security_zone_id: "my-routing-zone"
      vlan_id: 23
      ipv4_enabled: true
      ipv4_subnet: 192.0.2.0/24
      virtual_gateway_ipv4_enabled: true
      virtual_gateway_ipv4: 192.0.2.254/24
      bound_to:
        - system_id: "spine1"
    state: present

# Global vlan_id — applies to every bound_to entry that has no per-device override
- name: Create virtual network with global VLAN ID
  juniper.apstra.virtual_network:
    id:
      blueprint: "my-blueprint"
    body:
      label: "prod-vn"
      vn_type: "vxlan"
      vlan_id: 100
      bound_to:
        - system_id: "leaf1"
        - system_id: "leaf2"
        - system_id: "leaf3"
          vlan_id: 200    # per-device override wins
    state: present

# ESI pair expansion — specify the redundancy-group name; the module expands
# it into the two member devices automatically
- name: Create virtual network bound to ESI pair
  juniper.apstra.virtual_network:
    id:
      blueprint: "my-blueprint"
    body:
      label: "esi-vn"
      vn_type: "vxlan"
      vlan_id: 300
      bound_to:
        - system_id: "apstra_esi_001_leaf_pair1"   # ESI redundancy group
    state: present

# create_policy_tagged — use when you want ONLY a tagged CT and no auto-untagged CT.
# Without this, Apstra normally expects an untagged CT; by default the module sets
# create_policy_untagged=True automatically for vxlan VNs.  Setting
# create_policy_tagged=True explicitly suppresses that auto-injection so only one
# tagged connectivity template is created (avoids the unexpected extra VLAN from pool).
- name: Create virtual network with tagged-only connectivity template
  juniper.apstra.virtual_network:
    id:
      blueprint: "my-blueprint"
    body:
      label: "prod-vn-tagged"
      vn_type: "vxlan"
      vlan_id: 254
      create_policy_tagged: true   # suppresses auto create_policy_untagged injection
      security_zone_id: "Tenant1"
      bound_to:
        - system_id: "DC1-Leaf1"
        - system_id: "DC1-Leaf2"
    state: present

- name: Delete a virtual network
  juniper.apstra.virtual_network:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      virtual_network: "AjAuUuVLylXCUgAqaQ"
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
  description: The virtual network object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the created virtual network.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "virtual_network": "AjAuUuVLylXCUgAqaQ"
  }
virtual_network:
  description: The virtual network object details.
  returned: on create or update
  type: dict
  sample: {
      "id": "AjAuUuVLylXCUgAqaQ",
      "label": "Test-VN-label",
      "description": "test VN description",
      "ipv4_enabled": true,
      "virtual_gateway_ipv4_enabled": true,
      "vn_id": "16777214",
      "vn_type": "vxlan"
  }
tag_response:
  description: The response from applying tags to the virtual network.
  type: list
  returned: when tags are applied
  sample: ["red", "blue"]
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
    resolve_system_node_id,
    resolve_security_zone_id,
    resolve_esi_member_ids,
)


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        tags=dict(type="list", elements="str", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        object_type = "blueprints.virtual_networks"
        leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]
        tags = module.params.get("tags", None)

        # Resolve blueprint name to ID if needed
        if "blueprint" in id:
            id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])

        # Coerce integer fields that the API requires as int, not str
        # Note: vn_id must remain a string per the API spec
        if body:
            for int_field in ("l3_mtu",):
                if int_field in body and body[int_field] is not None:
                    body[int_field] = int(body[int_field])
            # Ensure vn_id is a string
            if "vn_id" in body and body["vn_id"] is not None:
                body["vn_id"] = str(body["vn_id"])
            # Feature: consume top-level vlan_id as global default for bound_to
            # entries.  The value is stripped from body before the API call so it
            # is never forwarded to Apstra as a VN-level field.
            # When bound_to is absent, vlan_id is kept in body and passed through
            # to the API as a VN-level field (existing behaviour).
            global_vlan_id = None
            if "vlan_id" in body and "bound_to" in body:
                global_vlan_id = body.pop("vlan_id")
                if global_vlan_id is not None:
                    global_vlan_id = int(global_vlan_id)
            elif "vlan_id" in body and body["vlan_id"] is not None:
                body["vlan_id"] = int(body["vlan_id"])

            # Process bound_to: normalise, apply global vlan_id default,
            # expand ESI redundancy groups, and resolve system names to IDs.
            if "bound_to" in body and isinstance(body["bound_to"], list):
                bp_id = id.get("blueprint")
                expanded = []
                for entry in body["bound_to"]:
                    # Normalise string shorthand
                    if isinstance(entry, str):
                        entry = {"system_id": entry}
                    else:
                        entry = dict(entry)  # shallow copy — avoid mutating params

                    # Coerce per-entry vlan_id to int
                    if "vlan_id" in entry and entry["vlan_id"] is not None:
                        entry["vlan_id"] = int(entry["vlan_id"])

                    # Apply global vlan_id when the entry carries no override
                    if global_vlan_id is not None and "vlan_id" not in entry:
                        entry["vlan_id"] = global_vlan_id

                    if "system_id" in entry and bp_id:
                        sys_ref = entry["system_id"]
                        # Check if this is an ESI/MLAG redundancy group:
                        # if so, expand into one entry per member device.
                        member_ids = resolve_esi_member_ids(
                            client_factory, bp_id, sys_ref
                        )
                        if member_ids is not None:
                            for mbr_id in member_ids:
                                mbr_entry = dict(entry)
                                mbr_entry["system_id"] = mbr_id
                                expanded.append(mbr_entry)
                        else:
                            # Regular system node — resolve label to graph ID
                            entry["system_id"] = resolve_system_node_id(
                                client_factory, bp_id, sys_ref
                            )
                            expanded.append(entry)
                    else:
                        expanded.append(entry)

                body["bound_to"] = expanded

            # Resolve security_zone_id by label if needed
            if "security_zone_id" in body:
                bp_id = id.get("blueprint")
                if bp_id:
                    body["security_zone_id"] = resolve_security_zone_id(
                        client_factory, bp_id, body["security_zone_id"]
                    )

            # Ensure Apstra generates the "Untagged VxLAN" connectivity template
            # for vxlan virtual networks.  Without create_policy_untagged=True the
            # auto-generated CT is not created, so host interfaces cannot be
            # assigned to the VN.  The field is write-only (not returned by GET),
            # so compare_and_update() silently skips it on updates, preserving
            # full idempotency.  Callers may override by setting the field
            # explicitly to False in the body.
            #
            # Do NOT add create_policy_untagged when create_policy_tagged is
            # True — the caller explicitly wants a tagged CT only.  Adding both
            # would cause Apstra to create a second (untagged) CT with an
            # auto-assigned VLAN from the pool, producing an unexpected extra
            # VLAN assignment visible in the UI.
            if (
                body.get("vn_type") == "vxlan"
                and "create_policy_untagged" not in body
                and not body.get("create_policy_tagged")
            ):
                body["create_policy_untagged"] = True

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
        if object_id is None:
            if (body is not None) and ("label" in body):
                id_found = client_factory.get_id_by_label(
                    id["blueprint"], leaf_object_type, body["label"]
                )
                if id_found:
                    id[leaf_object_type] = id_found
                    current_object = client_factory.object_request(
                        object_type, "get", id
                    )
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

            # Apply tags if specified
            if tags:
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

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(f"Cannot manage a {leaf_object_type} without a object id")

        if state == "absent":
            # Delete the blueprint
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
