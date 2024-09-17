#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

DOCUMENTATION = '''
---
module: blueprint
short_description: Manage Apstra blueprints
description:
    - This module allows you to create, lock, unlock, and delete Apstra blueprints.
version_added: "1.0.0"
author: "Edwin Jacques (@edwinpjacques)"
options:
    id:
        description:
            - The ID of the blueprint.
        required: false
        type: dict
    resource:
        description:
            - A dictionary representing the blueprint to create.
        required: false
        type: dict
    lock_state:
        description:
            - Status to transition lock to. To "lock", must be in the "unlocked" state (and vice versa).
        required: false
        type: str
        choices: ["locked", "unlocked", "ignore"]
        default: "locked"
    lock_timeout:
        description:
            - The timeout in seconds for locking the blueprint.
        required: false
        type: int
        default: 60
    state:
        description:
            - The desired state of the blueprint.
        required: false
        type: str
        choices: ["present", "absent"]
        default: "present"
extends_documentation_fragment:
    - junipernetworks.apstra.apstra_client
'''

EXAMPLES = '''
# Create a new blueprint
- name: Create blueprint
  blueprint:
    resource:
      name: example_blueprint
      design: two_stage_l3clos
    state: present

# Delete a blueprint
- name: Delete blueprint
  blueprint:
    id:
        blueprint: blueprint-123
    state: absent

# Lock a blueprint
- name: Lock blueprint
  blueprint:
    id:
        blueprint: blueprint-123
    state: present

# Unlock a blueprint
- name: Unlock blueprint
  blueprint:
    id:
        blueprint: blueprint-123
    lock_state: unlocked
    state: present
'''

RETURN = '''
blueprint:
    description: The blueprint object.
    returned: always
    type: dict
    sample: {
        "id": "blueprint-123",
        "name": "example_blueprint",
        "design": "two_stage_l3clos"
    }
changed:
    description: Whether the blueprint was changed.
    returned: always
    type: bool
    sample: true
lock_state:
    description: State of the blueprint lock.
    returned: always
    type: str
    sample: "locked"
msg:
    description: A message describing the result.
    returned: always
    type: str
    sample: "Blueprint created successfully"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    DEFAULT_BLUEPRINT_LOCK_TIMEOUT
)
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.resource import compare_and_update

def main():
    blueprint_module_args = dict(
        id=dict(type="dict", required=False),
        resource=dict(type="dict", required=False),
        lock_state=dict(type="str", required=False, choices=["locked", "unlocked", "ignore"], default="locked"),
        lock_timeout=dict(type="int", required=False, default=DEFAULT_BLUEPRINT_LOCK_TIMEOUT),
        unlock=dict(type="bool", required=False, default=False),
        state=dict(type="str", required=False, choices=["present", "absent"], default="present"),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | blueprint_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module.params)
        
        # Get the id if specified
        id = module.params.get("id", None)
        resource = module.params.get("resource", None)
        state = module.params["state"]
        lock_state = module.params["lock_state"]
        lock_timeout = module.params["lock_timeout"]

        # Make the requested changes
        if state == "present":
            if id is None:
                if resource is None:
                    raise ValueError("Must specify 'resource' to create a blueprint")
                # Create the resource
                created_blueprint = client_factory.resources_op("blueprints", "create", {}, resource)
                id = created_blueprint["id"]
                result["changed"] = True
                result["blueprint"] = created_blueprint
            
        # Lock the resource if requested
        if lock_state == "locked":
            module.log("Locking blueprint")
            client_factory.lock_blueprint(id=id, timeout=lock_timeout)
            
        if state == "absent":
            if id is None:
                raise ValueError("Cannot delete a blueprint without a resource id")
            # Delete the blueprint
            client_factory.resources_op("blueprints", "delete", {"blueprint": id})
            result["changed"] = True

        # Unlock the blueprint if requested
        if lock_state == "unlocked":
            client_factory.unlock_blueprint(id=id, timeout=lock_timeout)
        elif state == "absent":
            # If the blueprint is deleted, it will be unlocked (tag deleted)
            lock_state = "unlocked"

        # Always report the lock state
        result["lock_state"] = lock_state
        
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()