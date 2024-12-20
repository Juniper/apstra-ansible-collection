#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

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
  junipernetworks.apstra.resource_group:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      group_type: "ip"
      group_name: "sz:s1dQM4lDL8BBfxOsYQ,leaf_loopback_ips"
    body:
      pool_ids:
        - "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        - "77777777-7f37-7e17-7d57-7f9c26f16967"
    state: present

- name: Delete a resource group
  junipernetworks.apstra.resource_group:
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


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    singular_leaf_object_type,
)
import traceback


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

            # Return the final object state
            result[leaf_object_type] = current_object

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
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
