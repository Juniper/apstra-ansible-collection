#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: resource_group
short_description: Manage resource groups in Apstra
version_added: "0.1.0"
author:
  - "Edwin Jacques (@edwinpjacques)"
description:
  - This module allows you to update, and delete resource groups in Apstra.
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
      - Dictionary containing the blueprint and resource group IDs.
      - To identify the resource group, the resource_type and group_name fields are required.
      - When creating a resource group, only the blueprint field is required, other fields
      - are specified in the body.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the resource group object details.
    required: false
    type: dict
  state:
    description:
      - Desired state of the resource group.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Update a resource group
  juniper.apstra.resource_group:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      group_type: "ip"
      group_name: "sz:s1dQM4lDL8BBfxOsYQ,leaf_loopback_ips"
    body:
      pool_ids:
        - "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        - "77777777-7f37-7e17-7d57-7f9c26f16967"
    state: present

# Use pool display names instead of UUIDs — names are resolved automatically
- name: Update resource group using pool names
  juniper.apstra.resource_group:
    id:
      blueprint: "my-blueprint"
      group_type: "asn"
      group_name: "spine_asns"
    body:
      pool_ids:
        - "vpod-evpn-asn-pool"
    state: present

# Use blueprint name instead of UUID
- name: Update resource group using blueprint name
  juniper.apstra.resource_group:
    id:
      blueprint: "my-blueprint"
      group_type: "ip"
      group_name: "leaf_loopback_ips"
    body:
      pool_ids:
        - "my-ip-pool"
    state: present

- name: Delete a resource group
  juniper.apstra.resource_group:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      group_type: "ip"
      group_name: "sz:s1dQM4lDL8BBfxOsYQ,leaf_loopback_ips"
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
  description: The resource group object details.
  type: dict
  returned: when state is present and changes are made
resource_group:
  description: The resource group object details.
  returned: on create or update
  type: dict
  sample: {
      type: "ip",
      name: "sz:s1dQM4lDL8BBfxOsYQ,leaf_loopback_ips",
      pool_ids: [
        "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      ]
    }
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
    resolve_pool_ids,
    resolve_resource_group_name,
)


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        object_type = "blueprints.resource_groups"
        leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]

        # Resolve blueprint name to ID if needed
        if "blueprint" in id:
            id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])

        # Resolve pool_ids by display_name if needed
        group_type = id.get("group_type")
        if body and "pool_ids" in body and group_type:
            body["pool_ids"] = resolve_pool_ids(
                client_factory, body["pool_ids"], group_type
            )

        # Validate the id
        if "blueprint" not in id:
            raise ValueError("Must specify 'blueprint' in id")
        if state == "absent" and ("group_type" not in id or "group_name" not in id):
            raise ValueError(
                "Must specify 'group_type' and 'group_name' in id to delete a resource group"
            )
        group_type = id.get("group_type", None)
        group_name = id.get("group_name", None)

        if group_type is None or group_name is None:
            raise ValueError(
                f"Must specify 'group_type' and 'group_name' in id to manage a {leaf_object_type}"
            )

        # Resolve security-zone name in group_name (e.g. "sz:VRF1,leaf_loopback_ips")
        group_name = resolve_resource_group_name(
            client_factory, id["blueprint"], group_name
        )
        id["group_name"] = group_name

        # Get the object
        ra_client = client_factory.get_resource_allocation_client()
        resource_group = ra_client.blueprints[id["blueprint"]].resource_groups[
            group_type
        ][group_name]

        # Make the requested changes
        if state == "present":
            current_object = None
            current_object = resource_group.get()

            if current_object:
                # Apstra omits pool_ids from the GET response when no pools are
                # assigned.  compare_and_update() at depth-0 silently skips keys
                # absent in current, so we normalise here to ensure an empty
                # assignment is treated as a genuine change target.
                if "pool_ids" not in current_object:
                    current_object["pool_ids"] = []

                if body:
                    # Update the object
                    changes = {}
                    if client_factory.compare_and_update(current_object, body, changes):
                        updated_object = resource_group.update(changes)
                        result["changed"] = True
                        if updated_object:
                            result["response"] = updated_object
                        result["changes"] = changes
                        result["msg"] = f"{leaf_object_type} updated successfully"
                    else:
                        result["changed"] = False
                        result["msg"] = (
                            f"{leaf_object_type} already up to date, no changes needed"
                        )
            elif body:
                # Resource group does not exist yet (e.g. VRF-scoped groups
                # like "sz:<sz_id>,leaf_loopback_ips" are not pre-created).
                # A PUT will create the assignment.
                updated_object = resource_group.update(body)
                result["changed"] = True
                if updated_object:
                    result["response"] = updated_object
                result["changes"] = body
                result["msg"] = f"{leaf_object_type} created successfully"
                # Re-read to populate current_object after creation
                current_object = resource_group.get()

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
