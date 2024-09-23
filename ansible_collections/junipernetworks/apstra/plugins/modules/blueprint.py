#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    DEFAULT_BLUEPRINT_LOCK_TIMEOUT,
    DEFAULT_BLUEPRINT_COMMIT_TIMEOUT,
)
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.object import (
    compare_and_update,
)

DOCUMENTATION = """
---
module: blueprint
short_description: Manage Apstra blueprints
description:
    - This module allows you to create, lock, unlock, and delete Apstra blueprints.
version_added: "0.1.0"
author: "Edwin Jacques (@edwinpjacques)"
options:
  api_url:
    description:
      - The url used to access the Apstra api.
    type: str
    required: false
    default: APSTRA_API_URL environment variable
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
      - The ID of the blueprint.
    required: false
    type: dict
  body:
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
    default: {lock_timeout}
  commit_timeout:
    description:
      - The timeout in seconds for committing the blueprint.
    required: false
    type: int
    default: {commit_timeout}
  state:
    description:
      - The desired state of the blueprint.
    required: false
    type: str
    choices: ["present", "committed", "absent"]
    default: "present"
extends_documentation_fragment:
    - junipernetworks.apstra.apstra_client
""".format(
    lock_timeout=DEFAULT_BLUEPRINT_LOCK_TIMEOUT,
    commit_timeout=DEFAULT_BLUEPRINT_COMMIT_TIMEOUT,
)

EXAMPLES = """
# Create a new blueprint
- name: Create blueprint
  blueprint:
    response:
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
"""

RETURN = """
changed:
    description: Whether the blueprint was changed.
    returned: always
    type: bool
    sample: true
id:
    description: The ID of the created blueprint.
    returned: on create
    type: dict
    sample: {
        "id": "blueprint-123"
    }
msg:
    description: A message describing the result.
    returned: always
    type: str
    sample: "blueprint created successfully"
lock_state:
    description: State of the blueprint lock.
    returned: always
    type: str
    sample: "locked"
response:
    description: The response from the Apstra API.
    returned: on create
    type: dict
    sample: {
        "id": "blueprint-123",
    }
"""


def main():
    blueprint_module_args = dict(
        id=dict(type="dict", required=False),
        body=dict(type="dict", required=False),
        lock_state=dict(
            type="str",
            required=False,
            choices=["locked", "unlocked", "ignore"],
            default="locked",
        ),
        lock_timeout=dict(
            type="int", required=False, default=DEFAULT_BLUEPRINT_LOCK_TIMEOUT
        ),
        commit_timeout=dict(
            type="int", required=False, default=DEFAULT_BLUEPRINT_COMMIT_TIMEOUT
        ),
        unlock=dict(type="bool", required=False, default=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "committed", "absent"],
            default="present",
        ),
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
        blueprint_id = id.get("blueprint", None) if id is not None else None
        body = module.params.get("body", None)
        state = module.params["state"]
        lock_state = module.params["lock_state"]
        lock_timeout = module.params["lock_timeout"]
        commit_timeout = module.params["commit_timeout"]

        # Make the requested changes
        if state != "absent":
            if id is None:
                if body is None:
                    raise ValueError("Must specify 'body' to create a blueprint")
                # Create the object
                created_blueprint = client_factory.object_request(
                    "blueprints", "create", {}, body
                )
                blueprint_id = created_blueprint["id"]
                id = {"blueprint": blueprint_id}
                result["id"] = id
                result["changed"] = True
                result["response"] = created_blueprint
                result["msg"] = "blueprint created successfully"

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError("Cannot manage a blueprint without a object id")

        # Lock the object if requested
        if lock_state == "locked" and state != "absent":
            module.log("Locking blueprint")
            client_factory.lock_blueprint(id=blueprint_id, timeout=lock_timeout)

        if state == "absent":
            if id is None:
                raise ValueError("Cannot delete a blueprint without a object id")
            # Delete the blueprint
            client_factory.object_request("blueprints", "delete", id)
            result["changed"] = True
            result["msg"] = "blueprint deleted successfully"

        if state == "committed":
            # Commit the blueprint
            client_factory.commit_blueprint(id=blueprint_id, timeout=commit_timeout)
            result["changed"] = True
            result["msg"] = "blueprint committed successfully"

        # Unlock the blueprint if requested
        if state == "absent":
            # If the blueprint is deleted, it will be unlocked (tag deleted)
            lock_state = "unlocked"
        elif lock_state == "unlocked":
            client_factory.unlock_blueprint(id=blueprint_id)

        # Always report the lock state
        result["lock_state"] = lock_state

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
