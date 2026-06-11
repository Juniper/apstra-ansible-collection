#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: rbac_user
short_description: Manage platform RBAC users in Apstra
version_added: "1.1.0"
author:
  - "Shirish Ranoji (@sranoji)"
description:
  - Manage platform (controller-level) users in Apstra.
  - Maps to C(/api/aaa/users) and C(/api/aaa/users/{id}/roles).
  - Users are identified by C(username); the module looks up the
    user UUID automatically.
options:
  api_url:
    description: Apstra API URL. Defaults to C(APSTRA_API_URL) env var.
    type: str
    required: false
  verify_certificates:
    description: Verify TLS certificates.
    type: bool
    required: false
    default: true
  username:
    description: Apstra username for SDK login. Defaults to C(APSTRA_USERNAME) env var.
    type: str
    required: false
  password:
    description: Apstra password for SDK login. Defaults to C(APSTRA_PASSWORD) env var.
    type: str
    required: false
  auth_token:
    description: Pre-existing auth token. Defaults to C(APSTRA_AUTH_TOKEN) env var.
    type: str
    required: false
  id:
    description: Optional id dict; usually omitted because the user is identified by C(body.username).
    type: dict
    required: false
  body:
    description:
      - User definition.
      - Required key for every operation - C(username).
      - On create - also C(password). Optional - C(first_name), C(last_name), C(email), C(roles).
      - On update - any subset of the above (except C(password), which is handled via C(change_password)).
      - To rotate a password, supply C(change_password.old) and C(change_password.new).
    type: dict
    required: false
  state:
    description: Desired state.
    type: str
    required: false
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Create alice with viewer role
  juniper.apstra.rbac_user:
    body:
      username: alice
      password: "S3cret!Pass"
      first_name: Alice
      last_name: Liddell
      email: alice@example.com
      roles: [viewer]
    state: present

- name: Rename alice
  juniper.apstra.rbac_user:
    body:
      username: alice
      first_name: "Alice (mgr)"
    state: present

- name: Promote alice
  juniper.apstra.rbac_user:
    body:
      username: alice
      roles: [administrator]
    state: present

- name: Rotate password
  juniper.apstra.rbac_user:
    body:
      username: alice
      change_password:
        old: "S3cret!Pass"
        new: "S3cret!Pass2"
    state: present

- name: Delete alice
  juniper.apstra.rbac_user:
    body:
      username: alice
    state: absent
"""

RETURN = """
changed:
  description: Whether any change was made.
  type: bool
  returned: always
id:
  description: Resolved user id dict.
  type: dict
  returned: when user exists
user:
  description: Full user object.
  type: dict
  returned: when state is present
changes:
  description: Fields changed during update.
  type: dict
  returned: on update
msg:
  description: Result message.
  type: str
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

_PROFILE_FIELDS = ("first_name", "last_name", "email")


def _get_user(client, user_id):
    try:
        return client.users[user_id].get()
    except Exception:
        return None


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False),
        body=dict(type="dict", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
    )
    module_args = apstra_client_module_args() | object_module_args

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        factory = ApstraClientFactory.from_params(module)
        base = factory.get_base_client()

        body = module.params.get("body") or {}
        state = module.params["state"]
        id_param = module.params.get("id") or {}

        user_id = id_param.get("user")
        username = body.get("username")
        if not user_id and not username:
            module.fail_json(msg="Either id.user or body.username is required")

        if not user_id:
            user_id = factory.get_user_id_by_username(username)

        current = _get_user(base, user_id) if user_id else None

        # state == absent
        if state == "absent":
            if not current:
                module.exit_json(changed=False, msg="user already absent")
            if not module.check_mode:
                base.users[user_id].delete()
            module.exit_json(
                changed=True,
                id={"user": user_id},
                msg=f"user '{username or user_id}' deleted",
            )

        # state == present, CREATE
        if not current:
            if not username:
                module.fail_json(msg="body.username is required to create a user")
            if not body.get("password"):
                module.fail_json(msg="body.password is required to create a user")

            create_body = {"username": username, "password": body["password"]}
            for f in _PROFILE_FIELDS:
                if body.get(f) is not None:
                    create_body[f] = body[f]
            if body.get("roles") is not None:
                create_body["roles"] = list(body["roles"])

            if module.check_mode:
                module.exit_json(
                    changed=True,
                    id={"user": None},
                    msg=f"would create user '{username}'",
                )

            created = base.users.create(create_body)
            user_id = created["id"]
            final = _get_user(base, user_id) or {}
            module.exit_json(
                changed=True,
                id={"user": user_id},
                user=final,
                msg=f"user '{username}' created",
            )

        # state == present, UPDATE
        changes = {}

        profile_patch = {}
        for f in _PROFILE_FIELDS:
            if f in body and body[f] != current.get(f):
                profile_patch[f] = body[f]
        if profile_patch:
            if not module.check_mode:
                base.users[user_id].patch(profile_patch)
            changes.update(profile_patch)

        if "roles" in body and body["roles"] is not None:
            desired = sorted(body["roles"])
            actual = sorted(current.get("roles") or [])
            if desired != actual:
                if not module.check_mode:
                    base.users[user_id].roles.update({"roles": list(body["roles"])})
                changes["roles"] = list(body["roles"])

        cp = body.get("change_password")
        if cp:
            old_pw = cp.get("old")
            new_pw = cp.get("new")
            if not old_pw or not new_pw:
                module.fail_json(
                    msg="body.change_password requires both 'old' and 'new'"
                )
            if not module.check_mode:
                base.users[user_id].change_password(old_pw, new_pw)
            changes["password"] = "<changed>"

        if not changes:
            module.exit_json(
                changed=False,
                id={"user": user_id},
                user=current,
                msg=f"user '{username}' already up to date",
            )

        final = _get_user(base, user_id) or current
        module.exit_json(
            changed=True,
            id={"user": user_id},
            user=final,
            changes=changes,
            msg=f"user '{username}' updated",
        )

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"rbac_user exception: {e}\n{tb}")
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
