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
module: security_zone

short_description: Manage security zones in Apstra

version_added: "0.1.0"

author:
  - "Edwin Jacques (@edwinpjacques)"

description:
  - This module allows you to create, update, and delete security zones in Apstra.

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
      - Dictionary containing the blueprint and security zone IDs.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the security zone object details.
    required: false
    type: dict
  tags:
    description:
      - List of tags to apply to the security zone.
  state:
    description:
      - Desired state of the security zone.
    required: false
    type: str
    choices: ["present", "absent"]
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
tag_response:
  description: The response from applying tags to the security zone.
  type: list
  returned: when tags are applied
  sample: ["red", "blue"]
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        tags=dict(type="list", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

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

            # Return the final object state (may take a few tries)
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
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
