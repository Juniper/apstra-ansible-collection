#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.resource import (
    compare_and_update,
)

DOCUMENTATION = r"""
---
module: endpoint_policy_application_point

short_description: Manage endpoint policy application points in Apstra

version_added: "0.1.0"

author:
  - "Edwin Jacques (@edwinpjacques)"

description:
  - This module allows you to update and delete endpoint policy application points in Apstra.

options:
  id:
    description:
      - Dictionary containing the blueprint, endpoint policy and application point IDs.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the endpoint policy application point resource details.
    required: false
    type: dict
  state:
    description:
      - Desired state of the endpoint policy application point.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"

extends_documentation_fragment:
  - junipernetworks.apstra.apstra_client_module_args

"""

EXAMPLES = r"""
- name: Update a endpoint policy application point
  junipernetworks.apstra.endpoint_policy_application_point:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      endpoint_policy: "AjAuUuVLylXCUgAqaQ"
      application_point: "ABCuVLylXCUgA777"
    response:
      description: "test endpoint policy application point UPDATE"
    state: present

- name: Delete a endpoint policy application point
  junipernetworks.apstra.endpoint_policy_application_point:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      endpoint_policy_application_point: "AjAuUuVLylXCUgAqaQ"
    state: absent
"""

RETURN = r"""
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
id:
  description: The ID of the created endpoint policy application point.
  returned: on create
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "endpoint_policy": "1c8894c0-0d73-462b-a60e-59351cb42bba",
      "application_point": "AjAuUuVLylXCUgAqaQ"
  }
msg:
  description: The output message that the module generates.
  type: str
  returned: always
response:
    description: The response from the Apstra API.
    returned: on create
    type: dict
    sample: {
        "id": "1c8894c0-0d73-462b-a60e-59351cb42bba",
    }
"""


def main():
    resource_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | resource_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module.params)

        resource_type = "blueprints.obj_policy_application_points"
        singular_leaf_resource_type = client_factory.singular_leaf_resource_type(
            resource_type
        )

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]

        # Validate the id
        missing_id = client_factory.validate_id(resource_type, id)
        if len(missing_id) > 1 or (
            len(missing_id) == 1
            and state == "absent"
            and missing_id[0] != singular_leaf_resource_type
        ):
            raise ValueError(f"Invalid id: {id} for desired state of {state}.")
        resource_id = id.get(singular_leaf_resource_type, None)

        # Make the requested changes
        if state == "present":
            if resource_id is None:
                if body is None:
                    raise ValueError(
                        f"Must specify 'resource' to create a {singular_leaf_resource_type}"
                    )
                # Create the resource
                created_resource = client_factory.resources_op(
                    resource_type, "create", id, body
                )
                resource_id = created_resource["id"]
                id[singular_leaf_resource_type] = resource_id
                result["id"] = id
                result["changed"] = True
                result["response"] = created_resource
                result["msg"] = f"{singular_leaf_resource_type} created successfully"
            else:
                # Update the resource
                current_resource = client_factory.resources_op(resource_type, "get", id)
                changes = {}
                if compare_and_update(current_resource, body, changes):
                    updated_resource = client_factory.resources_op(
                        resource_type, "patch", id, changes
                    )
                    result["changed"] = True
                    result["response"] = updated_resource
                    result["msg"] = (
                        f"{singular_leaf_resource_type} updated successfully"
                    )

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(
                f"Cannot manage a {singular_leaf_resource_type} without a resource id"
            )

        if state == "absent":
            # Delete the blueprint
            client_factory.resources_op(resource_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{singular_leaf_resource_type} deleted successfully"

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
