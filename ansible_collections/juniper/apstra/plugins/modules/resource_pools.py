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
    singular_leaf_object_type,
)

DOCUMENTATION = """
---
module: resource_pools

short_description: Manage resource pools in Apstra

version_added: "0.1.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module allows you to create, update, and delete resource pools in Apstra.
  - Supported pool types are ASN, IP, IPv6, VLAN, and VNI.

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
  type:
    description:
      - The type of resource pool to manage.
    required: false
    type: str
    choices: ["asn", "ip", "ipv6", "vlan", "vni"]
    default: "asn"
  id:
    description:
      - Dictionary containing the resource pool ID.
    required: false
    type: dict
  body:
    description:
      - Dictionary containing the resource pool object details.
      - For ASN pools, use 'ranges' with 'first' and 'last' integer keys.
      - For IP pools, use 'subnets' with 'network' (CIDR notation) keys.
      - For IPv6 pools, use 'subnets' with 'network' (CIDR notation) keys.
      - For VLAN pools, use 'ranges' with 'first' and 'last' integer keys.
      - For VNI pools, use 'ranges' with 'first' and 'last' integer keys.
    required: false
    type: dict
  state:
    description:
      - Desired state of the resource pool.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Create an ASN pool (or update it if the display_name exists)
  juniper.apstra.resource_pools:
    type: asn
    body:
      display_name: "Test-ASN-Pool"
      ranges:
        - first: 65000
          last: 65100
    state: present

- name: Update an ASN pool
  juniper.apstra.resource_pools:
    type: asn
    id:
      asn_pool: "550e8400-e29b-41d4-a716-446655440000"
    body:
      display_name: "Updated-ASN-Pool"
      ranges:
        - first: 65000
          last: 65200
    state: present

- name: Delete an ASN pool
  juniper.apstra.resource_pools:
    type: asn
    id:
      asn_pool: "550e8400-e29b-41d4-a716-446655440000"
    state: absent

- name: Create an IP pool
  juniper.apstra.resource_pools:
    type: ip
    body:
      display_name: "Test-IP-Pool"
      subnets:
        - network: "10.100.0.0/16"
    state: present

- name: Update an IP pool
  juniper.apstra.resource_pools:
    type: ip
    id:
      ip_pool: "550e8400-e29b-41d4-a716-446655440000"
    body:
      display_name: "Updated-IP-Pool"
      subnets:
        - network: "10.100.0.0/16"
        - network: "10.200.0.0/16"
    state: present

- name: Delete an IP pool
  juniper.apstra.resource_pools:
    type: ip
    id:
      ip_pool: "550e8400-e29b-41d4-a716-446655440000"
    state: absent

- name: Create a VLAN pool
  juniper.apstra.resource_pools:
    type: vlan
    body:
      display_name: "Test-VLAN-Pool"
      ranges:
        - first: 100
          last: 200
    state: present

- name: Update a VLAN pool
  juniper.apstra.resource_pools:
    type: vlan
    id:
      vlan_pool: "550e8400-e29b-41d4-a716-446655440000"
    body:
      display_name: "Updated-VLAN-Pool"
      ranges:
        - first: 100
          last: 300
    state: present

- name: Delete a VLAN pool
  juniper.apstra.resource_pools:
    type: vlan
    id:
      vlan_pool: "550e8400-e29b-41d4-a716-446655440000"
    state: absent

- name: Create an IPv6 pool
  juniper.apstra.resource_pools:
    type: ipv6
    body:
      display_name: "Test-IPv6-Pool"
      subnets:
        - network: "fc01:a05:fab::/48"
    state: present

- name: Update an IPv6 pool
  juniper.apstra.resource_pools:
    type: ipv6
    id:
      ipv6_pool: "550e8400-e29b-41d4-a716-446655440000"
    body:
      display_name: "Updated-IPv6-Pool"
      subnets:
        - network: "fc01:a05:fab::/48"
        - network: "fc01:a05:fac::/48"
    state: present

- name: Delete an IPv6 pool
  juniper.apstra.resource_pools:
    type: ipv6
    id:
      ipv6_pool: "550e8400-e29b-41d4-a716-446655440000"
    state: absent

- name: Create a VNI pool
  juniper.apstra.resource_pools:
    type: vni
    body:
      display_name: "Test-VNI-Pool"
      ranges:
        - first: 5000
          last: 6000
    state: present

- name: Update a VNI pool
  juniper.apstra.resource_pools:
    type: vni
    id:
      vni_pool: "550e8400-e29b-41d4-a716-446655440000"
    body:
      display_name: "Updated-VNI-Pool"
      ranges:
        - first: 5000
          last: 7000
    state: present

- name: Delete a VNI pool
  juniper.apstra.resource_pools:
    type: vni
    id:
      vni_pool: "550e8400-e29b-41d4-a716-446655440000"
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
  description: The resource pool object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the resource pool.
  returned: on create, or when object identified by display_name
  type: dict
  sample: {
      "asn_pool": "550e8400-e29b-41d4-a716-446655440000"
  }
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

# Map pool type to the object type used by the client
POOL_TYPE_MAP = {
    "asn": "asn_pools",
    "ip": "ip_pools",
    "ipv6": "ipv6_pools",
    "vlan": "vlan_pools",
    "vni": "vni_pools",
}

# The list field that holds the pool entries differs by pool type
# ASN and VLAN pools use "ranges", IP pools use "subnets"
POOL_LIST_FIELD = {
    "asn": "ranges",
    "ip": "subnets",
    "ipv6": "subnets",
    "vlan": "ranges",
    "vni": "ranges",
}

# Read-only fields returned by the API inside each range/subnet entry
RANGE_READ_ONLY_FIELDS = ("status", "total", "used", "used_percentage")

# Read-only top-level fields returned by the API
OBJECT_READ_ONLY_FIELDS = (
    "id",
    "total",
    "used",
    "used_percentage",
    "status",
    "created_at",
    "last_modified_at",
    "tags",
)


def _strip_read_only_from_list_field(current_object, list_field):
    """Strip read-only fields from ranges/subnets so comparison is accurate."""
    if list_field in current_object and isinstance(current_object[list_field], list):
        current_object[list_field] = [
            {k: v for k, v in entry.items() if k not in RANGE_READ_ONLY_FIELDS}
            for entry in current_object[list_field]
        ]


def main():
    object_module_args = dict(
        type=dict(
            type="str",
            required=False,
            choices=["asn", "ip", "ipv6", "vlan", "vni"],
            default="asn",
        ),
        id=dict(type="dict", required=False, default=None),
        body=dict(type="dict", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        pool_type = module.params["type"]
        object_type = POOL_TYPE_MAP[pool_type]
        list_field = POOL_LIST_FIELD[pool_type]
        leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params - id can be None when not provided, so default to empty dict
        id = module.params.get("id")
        if id is None:
            id = {}
        body = module.params.get("body", None)
        state = module.params["state"]

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
            # Try to find by display_name if provided in body
            display_name = body.get("display_name") if body else None
            if display_name:
                try:
                    # Get all pools
                    all_pools_response = client_factory.object_request(
                        object_type, "list", {}, data={"display_name": display_name}
                    )

                    # Extract items from response
                    items = []
                    if all_pools_response is not None:
                        if isinstance(all_pools_response, dict):
                            if "items" in all_pools_response:
                                items = all_pools_response["items"]
                            elif "id" in all_pools_response:
                                items = [all_pools_response]
                        elif isinstance(all_pools_response, list):
                            items = all_pools_response

                    # Search for matching display_name
                    for pool in items:
                        if isinstance(pool, dict):
                            if pool.get("display_name") == display_name:
                                object_id = pool["id"]
                                id[leaf_object_type] = object_id
                                current_object = pool
                                break
                except Exception as e:
                    module.debug(f"Error during list operation: {str(e)}")
                    # Continue - we'll create a new object if needed
        else:
            try:
                current_object = client_factory.object_request(object_type, "get", id)
            except Exception as e:
                module.debug(f"Error getting object by id: {str(e)}")
                current_object = None

        # Make the requested changes
        if state == "present":
            if current_object:
                result["id"] = id
                if body:
                    # Strip read-only fields from current_object ranges/subnets
                    # before comparison so that API-only fields don't cause
                    # false-positive change detection.
                    _strip_read_only_from_list_field(current_object, list_field)

                    # Update the object
                    changes = {}
                    if client_factory.compare_and_update(current_object, body, changes):
                        # Resource pools use PUT (via 'update') and require the full body
                        update_body = {
                            k: v
                            for k, v in current_object.items()
                            if k not in OBJECT_READ_ONLY_FIELDS
                        }
                        updated_object = client_factory.object_request(
                            object_type, "update", id, update_body
                        )
                        result["changed"] = True
                        if updated_object:
                            result["response"] = updated_object
                        result["changes"] = changes
                        result["msg"] = f"{leaf_object_type} updated successfully"
                    else:
                        result["changed"] = False
                        result["msg"] = f"No changes needed for {leaf_object_type}"
                else:
                    result["changed"] = False
                    result["msg"] = f"No changes specified for {leaf_object_type}"
            else:
                if body is None:
                    raise ValueError(
                        f"Must specify 'body' to create a {leaf_object_type}"
                    )
                # Create the object
                created_object = client_factory.object_request(
                    object_type, "create", id, body
                )

                # Handle the response
                if created_object and isinstance(created_object, dict):
                    object_id = created_object.get("id")
                    if object_id:
                        id[leaf_object_type] = object_id
                        result["id"] = id
                        result["changed"] = True
                        result["response"] = created_object
                        result["msg"] = f"{leaf_object_type} created successfully"
                    else:
                        raise ValueError(
                            f"Created object has no 'id' field: {created_object}"
                        )
                else:
                    raise ValueError(f"Unexpected create response: {created_object}")

            # Return the final object state (may take a few tries)
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type, op="get", id=id, retry=10, retry_delay=3
            )

        if state == "absent":
            if current_object is None:
                result["changed"] = False
                result["msg"] = f"{leaf_object_type} does not exist"
            else:
                # Delete the resource pool
                client_factory.object_request(object_type, "delete", id)
                result["changed"] = True
                result["msg"] = f"{leaf_object_type} deleted successfully"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
