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
    blueprint:
        description:
            - A dictionary representing the blueprint.
        required: true
        type: dict
    lock:
        description:
            - Whether to lock the blueprint after creation or update.
        required: false
        type: bool
        default: true
    lock_timeout:
        description:
            - The timeout in seconds for locking the blueprint.
        required: false
        type: int
        default: 60
    unlock:
        description:
            - Whether to unlock the blueprint after the operation.
        required: false
        type: bool
        default: true
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
    blueprint:
      name: example_blueprint
      design: l3clos
    state: present

# Delete a blueprint
- name: Delete blueprint
  blueprint:
    blueprint:
      id: blueprint-123
    state: absent

# Lock a blueprint
- name: Lock blueprint
  blueprint:
    blueprint:
      id: blueprint-123
    lock: true
    state: present

# Unlock a blueprint
- name: Unlock blueprint
  blueprint:
    blueprint:
      id: blueprint-123
    unlock: true
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
        "design": "l3clos"
    }
changed:
    description: Whether the blueprint was changed.
    returned: always
    type: bool
    sample: true
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
        blueprint=dict(type="dict", required=True),
        lock=dict(type="bool", required=False, default=True),
        lock_timeout=dict(type="int", required=False, default=DEFAULT_BLUEPRINT_LOCK_TIMEOUT),
        unlock=dict(type="bool", required=False, default=True),
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
        id = module.params["blueprint"].get("id", None)
        blueprint = module.params["blueprint"]
        state = module.params["state"]
        lock_timeout = module.params["lock_timeout"]

        # Make the requested changes
        if state == "present":
            if id is None:
                # Create the resource
                created_blueprint = client_factory.resources_op("blueprints", "create", {}, blueprint)
                id = created_blueprint["id"]
                result["changed"] = True
                result["blueprint"] = created_blueprint
            
            # Lock the resource if requested (even if it was just created)
            if module.params["lock"]:
                module.log("Locking blueprint")
                client_factory.lock_blueprint(id=id, timeout=lock_timeout)
            
            # If id was specified, nothing to do since we can't update a blueprint.
            if result.get("blueprint", None) is None:
                raise Exception("Cannot update a blueprint object")
        elif state == "absent":
            # Delete the blueprint
            client_factory.resources_op("blueprints", "delete", {"blueprints": id})
            result["changed"] = True

        # Unlock the blueprint if requested
        if module.params["unlock"]:
            if state == "present":
                client_factory.unlock_blueprint(id=id, timeout=lock_timeout)
            else:
                raise Exception("Cannot unlock a blueprint that is being deleted")
        
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()