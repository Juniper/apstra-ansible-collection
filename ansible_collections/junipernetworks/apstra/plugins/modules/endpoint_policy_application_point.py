#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.object import (
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
  - This module allows you to update the endpoint policy application points in Apstra.

options:
  id:
    description:
      - Dictionary containing the blueprint and endpoint policy IDs.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the endpoint policy application point object details.
    required: false
    type: dict

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
    body:
      application_points:
        - node_id: "AjAuUuVLylXCUgAqaQ"
          used: true
        - node_id: "ABCuVLylXCUgA777"
          used: false

"""

RETURN = r"""
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
msg:
  description: The output message that the module generates.
  type: str
  returned: always
response:
    description: The response from the Apstra API.
    returned: on update
    type: dict
"""


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module.params)

        object_type = "blueprints.obj_policy_application_points"
        singular_leaf_object_type = client_factory.singular_leaf_object_type(
            object_type
        )

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)

        # Validate the id
        missing_id = client_factory.validate_id(object_type, id)
        if len(missing_id) > 1 (
        ):
            raise ValueError(f"Invalid id: {id}.")
        object_id = id.get(singular_leaf_object_type, None)

        # Make the requested changes
        if state == "present":
            if object_id is None:
                if body is None:
                    raise ValueError(
                        f"Must specify 'body' to create a {singular_leaf_object_type}"
                    )
                # Create the object
                created_object = client_factory.object_request(
                    object_type, "create", id, body
                )
                object_id = created_object["id"]
                id[singular_leaf_object_type] = object_id
                result["id"] = id
                result["changed"] = True
                result["response"] = created_object
                result["msg"] = f"{singular_leaf_object_type} created successfully"
            else:
                # Update the object
                current_object = client_factory.object_request(object_type, "get", id)
                changes = {}
                if compare_and_update(current_object, body, changes):
                    updated_object = client_factory.object_request(
                        object_type, "patch", id, changes
                    )
                    result["changed"] = True
                    result["response"] = updated_object
                    result["msg"] = (
                        f"{singular_leaf_object_type} updated successfully"
                    )

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(
                f"Cannot manage a {singular_leaf_object_type} without a object id"
            )

        if state == "absent":
            # Delete the blueprint
            client_factory.object_request(object_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{singular_leaf_object_type} deleted successfully"

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
