#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

DOCUMENTATION = """
---
module: endpoint_policy_application_point
short_description: Manage endpoint policy application points
version_added: "0.1.0"
author:
  - "Edwin Jacques (@edwinpjacques)"
description:
  - This module allows you to update the endpoint policy application points in Apstra.
options:
  api_url:
    description:
      - The url used to access the Apstra api.
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
  logout:
    description:
      - If set to true, the module will log out the current session.
    type: bool
    default: false
  body:
    description:
      - Dictionary containing the endpoint policy application point object details.
    required: false
    type: dict
"""

EXAMPLES = """
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

RETURN = """
changed:
  description: Indicates whether the module has made any changes. True if successful.
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


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


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
        client_factory = ApstraClientFactory.from_params(module)

        object_type = "blueprints.endpoint_policies.application_points"
        singular_leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)

        # Validate the id
        missing_id = client_factory.validate_id(object_type, id)
        if len(missing_id) > 1:
            raise ValueError(f"Invalid id: {id}.")
        object_id = id.get("endpoint_policy")
        if object_id is None:
            raise ValueError(
                f"Cannot manage a {singular_leaf_object_type} without an endpoint policy id"
            )

        # Make the requested changes

        # Update the object
        updated_object = client_factory.object_request(object_type, "patch", id, body)
        result["changed"] = True
        result["response"] = updated_object

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
