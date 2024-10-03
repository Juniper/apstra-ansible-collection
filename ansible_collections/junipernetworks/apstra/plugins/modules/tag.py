#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

DOCUMENTATION = """
---
module: tag
short_description: Manage tags in Apstra
version_added: "0.1.6"
author:
  - "Edwin Jacques (@edwinpjacques)"
description:
  - This module allows you to create, update, and delete tags in Apstra.
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
      - Dictionary containing the blueprint and tag IDs.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the tag object details.
    required: false
    type: dict
  state:
    description:
      - Desired state of the tag.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Create a tag (or update it if the label exists)
  junipernetworks.apstra.tag:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "example_tag"
      description: "Example tag"
    state: present

- name: Update a tag
  junipernetworks.apstra.tag:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      tag: ""Ho9QACZ2tHyxsoWcBA""
    body:
      label: "example_tag_changed"
      description: "Example tag UPDATE"
    state: present

- name: Delete a tag
  junipernetworks.apstra.tag:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      tag: ""Ho9QACZ2tHyxsoWcBA""
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
  description: The tag object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the created tag.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "tag": "Ho9QACZ2tHyxsoWcBA"
  }
tag:
  description: The tag object details.
  type: dict
  returned: on create or update
  sample: {
      "id": "Ho9QACZ2tHyxsoWcBA",
      "label": "example_tag",
      "description": "Example tag"
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

        object_type = "blueprints.tags"
        leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params
        id = module.params["id"]
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

        # Make the requested changes
        if state == "present":
            current_object = None
            if object_id is None:
                if body is None:
                    raise ValueError(
                        f"Must specify 'body' to create a {leaf_object_type}"
                    )

                # See if the object label exists
                current_object = (
                    client_factory.object_request(object_type, "get", id, body)
                    if "label" in body
                    else None
                )
                if current_object:
                    id[leaf_object_type] = current_object["id"]
                    result["id"] = id
                else:
                    # Create the object
                    created_object = client_factory.object_request(
                        object_type, "create", id, body
                    )
                    object_id = created_object["id"]
                    id[leaf_object_type] = object_id
                    result["id"] = id
                    result["changed"] = True
                    result["response"] = created_object
                    result["msg"] = f"{leaf_object_type} created successfully"
            else:
                current_object = client_factory.object_request(object_type, "get", id)

            if current_object:
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
              
            # Return the final object state
            result[leaf_object_type] = client_factory.object_request(object_type, "get", id)

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(f"Cannot manage a {leaf_object_type} without a object id")

        if state == "absent":
            # Delete the blueprint
            client_factory.object_request(object_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{leaf_object_type} deleted successfully"

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
