#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: rollback

short_description: Manage blueprint rollback and revisions in Apstra

version_added: "0.1.0"

author:
  - "Vamsi Gavini (@vgavini)"

description:
  - This module allows you to rollback a blueprint to a specific revision,
    revert it to the latest backup, or list available revisions.
  - Uses the Apstra API endpoint POST /api/blueprints/{blueprint_id}/rollback.

options:
  api_url:
    description:
      - The URL used to access the Apstra api.
    type: str
    required: false
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
  password:
    description:
      - The password for authentication.
    type: str
    required: false
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  id:
    description:
      - Dictionary containing the blueprint ID.
      - Must include C(blueprint) key.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing rollback parameters.
      - Required for C(state=rolledback). Must include C(revision_id).
    required: false
    type: dict
  state:
    description:
      - Desired action to perform.
      - C(rolledback) rolls back the blueprint to a specific revision.
      - C(reverted) reverts the blueprint to the latest backup version.
      - C(listed) lists all available revisions (read-only).
    required: false
    type: str
    choices: ["rolledback", "reverted", "listed"]
    default: "rolledback"
"""

EXAMPLES = """
- name: List available revisions for a blueprint
  juniper.apstra.rollback:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    state: listed

- name: Rollback blueprint to a specific revision
  juniper.apstra.rollback:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      revision_id: "30"
    state: rolledback

- name: Revert blueprint to the latest backup version
  juniper.apstra.rollback:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    state: reverted
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
revisions:
  description: List of available blueprint revisions.
  type: list
  returned: when state is listed
  sample:
    - revision_id: "30"
      created_at: "2026-03-03T15:55:27.897696Z"
      user: "admin"
      user_ip: "10.108.28.45"
      description: ""
      user_saved: false
      auto_saved: true
revision_id:
  description: The revision ID that was rolled back to.
  type: str
  returned: when state is rolledback
response:
  description: The API response from the rollback or revert operation.
  type: dict
  returned: when state is rolledback or reverted
id:
  description: The blueprint ID dictionary.
  type: dict
  returned: always
  sample:
    blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["rolledback", "reverted", "listed"],
            default="rolledback",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]

        # Validate blueprint ID is provided
        blueprint_id = id.get("blueprint")
        if not blueprint_id:
            raise ValueError("'id.blueprint' is required for rollback operations")
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
        id["blueprint"] = blueprint_id

        result["id"] = id

        if state == "listed":
            # List all available revisions
            revisions = client_factory.list_revisions(blueprint_id)
            result["revisions"] = revisions
            result["changed"] = False
            result["msg"] = "Retrieved %d revisions" % len(revisions)

        elif state == "rolledback":
            # Rollback to a specific revision
            if body is None or "revision_id" not in body:
                raise ValueError(
                    "'body.revision_id' is required when state is 'rolledback'"
                )
            revision_id = str(body["revision_id"])
            response = client_factory.rollback_blueprint(blueprint_id, revision_id)
            result["changed"] = True
            result["revision_id"] = revision_id
            result["response"] = response
            result["msg"] = (
                "Blueprint rolled back to revision %s successfully" % revision_id
            )

        elif state == "reverted":
            # Revert to the latest backup version
            response = client_factory.revert_blueprint(blueprint_id)
            result["changed"] = True
            result["response"] = response
            result["msg"] = "Blueprint reverted to latest backup successfully"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
