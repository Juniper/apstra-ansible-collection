#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    singular_leaf_resource_type
)
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.resource import (
    compare_and_update,
)

DOCUMENTATION = r"""
---
module: security_zone

short_description: Manage security zones in Apstra

version_added: "0.1.0"

author:
  - "Edwin Jacques (@edwinpjacques)"

description:
  - This module allows you to create, update, and delete security zones in Apstra.

options:
  id:
    description:
      - Dictionary containing the blueprint and security zone IDs.
    required: true
    type: dict
  resource:
    description:
      - Dictionary containing the security zone resource details.
    required: false
    type: dict
  state:
    description:
      - Desired state of the security zone.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"

extends_documentation_fragment:
  - junipernetworks.apstra.apstra_client_module_args

"""

EXAMPLES = r"""
- name: Create a security zone
  junipernetworks.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    resource:
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

- name: Update a security zone
  junipernetworks.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      security_zone: "AjAuUuVLylXCUgAqaQ"
    resource:
      description: "example security zone UPDATE"
      import_policy: "extra_only"
    state: present

- name: Delete a security zone
  junipernetworks.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      security_zone: "AjAuUuVLylXCUgAqaQ"
    state: absent
"""

RETURN = r"""
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
resource:
  description: The security zone resource details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the created security zone.
  returned: on create
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "security_zone": "AjAuUuVLylXCUgAqaQ"
  }
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


def main():
    resource_module_args = dict(
        id=dict(type="dict", required=True),
        resource=dict(type="dict", required=False),
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

        resource_type = "blueprints.security_zones"
        leaf_resource_type = singular_leaf_resource_type(
            resource_type
        )

        # Validate params
        id = module.params["id"]
        resource = module.params.get("resource", None)
        state = module.params["state"]

        # Validate the id
        missing_id = client_factory.validate_id(resource_type, id)
        if len(missing_id) > 1 or (
            len(missing_id) == 1
            and state == "absent"
            and missing_id[0] != leaf_resource_type
        ):
            raise ValueError(f"Invalid id: {id} for desired state of {state}.")
        resource_id = id.get(leaf_resource_type, None)

        # Make the requested changes
        if state == "present":
            if resource_id is None:
                if resource is None:
                    raise ValueError(
                        f"Must specify 'resource' to create a {leaf_resource_type}"
                    )
                # Create the resource
                created_resource = client_factory.resources_op(
                    resource_type, "create", id, resource
                )
                resource_id = created_resource["id"]
                id[leaf_resource_type] = resource_id
                result["id"] = id
                result["changed"] = True
                result["resource"] = created_resource
                result["msg"] = f"{leaf_resource_type} created successfully"
            else:
                # Update the resource
                current_resource = client_factory.resources_op(resource_type, "get", id)
                changes = {}
                if compare_and_update(current_resource, resource, changes):
                    updated_resource = client_factory.resources_op(
                        resource_type, "patch", id, changes
                    )
                    result["changed"] = True
                    result["resource"] = updated_resource
                    result["msg"] = (
                        f"{leaf_resource_type} updated successfully"
                    )

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(
                f"Cannot manage a {leaf_resource_type} without a resource id"
            )

        if state == "absent":
            # Delete the blueprint
            client_factory.resources_op(resource_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{leaf_resource_type} deleted successfully"

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
