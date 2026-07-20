#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: rbac_roles
short_description: Manage platform RBAC roles in Apstra
version_added: "1.1.0"
author:
  - "Shirish Ranoji (@sranoji)"
description:
  - Manage platform (controller-level) RBAC roles in Apstra.
  - Maps to C(/api/aaa/roles).
  - Supports role create/update/delete with idempotency.
    - Role C(type) is mandatory for state C(present) and must be C(global) or C(granular).
    - Granular permission C(scope) accepts only shorthand blueprint values
        (a single blueprint id string or a list of blueprint ids), which the
        module expands to C(blueprint_id in [...]).
  - Permission payload supports direct C(body.permissions) or convenience keys
        C(global_permissions), C(granular_permissions)/C(blueprint_permissions), and
        C(tenant_permissions).
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
        description:
            - Optional role id dictionary.
            - C(id.role) can be a role UUID or role name.
        type: dict
        required: false
  body:
        description:
            - Role definition.
            - Required for state C(present).
            - Role identifier must be supplied via C(body.role) (or C(body.name) alias).
            - C(body.type) is required for state C(present) and must be C(global) or C(granular).
                        - For C(granular_permissions) and C(blueprint_permissions), C(scope)
                            must be a single blueprint id string or a list of blueprint ids.
                        - Full scope expressions (for example C(blueprint_id in [...])) are
                            rejected by this module.
            - Permission content can be passed as C(body.permissions) directly or split into
                C(global_permissions), C(granular_permissions)/C(blueprint_permissions), and
                C(tenant_permissions), which are merged into C(permissions).
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
- name: Create custom role with global + granular + tenant permissions
  juniper.apstra.rbac_roles:
        body:
            role: custom_role_ansible
            type: global
            label: custom_role_ansible
            description: Custom role from ansible
            global_permissions:
                aaa:
                    users: write
            granular_permissions:
                - scope:
                    - blueprint-id-1
                    - blueprint-id-2
                  permissions:
                    - rbac.blueprint.read
            tenant_permissions: []
        state: present

- name: Replace permissions in existing role
  juniper.apstra.rbac_roles:
        body:
            role: custom_role_ansible
                        type: global
            permissions:
                global: {}
                granular: []
                tenant: []
        state: present

- name: Delete custom role
  juniper.apstra.rbac_roles:
        body:
            role: custom_role_ansible
        state: absent
"""

RETURN = """
changed:
  description: Whether any change was made.
  type: bool
  returned: always
id:
  description: Resolved role id dict.
  type: dict
  returned: when role exists
role:
  description: Full role object.
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

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    ApstraClientFactory,
    apstra_client_module_args,
)


VALID_ROLE_TYPES = {"global", "granular"}


def _normalize(value):
    if isinstance(value, dict):
        return {k: _normalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        normalized_items = [_normalize(v) for v in value]
        return sorted(normalized_items, key=lambda x: json.dumps(x, sort_keys=True))
    return value


def _equal_semantic(left, right):
    return _normalize(left) == _normalize(right)


def _role_name_from_obj(role_obj):
    if not isinstance(role_obj, dict):
        return None
    return role_obj.get("role") or role_obj.get("label")


def _list_roles(base_client):
    roles = base_client.roles.list()
    if isinstance(roles, dict):
        return roles.get("items", [])
    return roles or []


def _find_role_by_name(base_client, role_name):
    if not role_name:
        return None
    for role_obj in _list_roles(base_client):
        if not isinstance(role_obj, dict):
            continue
        if role_obj.get("role") == role_name or role_obj.get("label") == role_name:
            role_id = role_obj.get("id")
            if role_id:
                return base_client.roles[role_id].get()
            return role_obj
    return None


def _resolve_role(base_client, factory, role_ref=None, role_name=None):
    role_id = None
    current = None

    if role_ref:
        if isinstance(role_ref, str) and "-" in role_ref:
            role_id = role_ref
            try:
                current = base_client.roles[role_id].get()
            except Exception:
                current = None
        else:
            current = _find_role_by_name(base_client, role_ref)
            if current:
                role_id = current.get("id")

    if not current and role_name:
        current = _find_role_by_name(base_client, role_name)
        if current:
            role_id = current.get("id")

    if not role_id and role_name:
        role_id = factory.get_role_id_by_name(role_name)
        if role_id and not current:
            try:
                current = base_client.roles[role_id].get()
            except Exception:
                current = None

    return role_id, current


def _normalize_blueprint_scope(scope):
    def _validate_blueprint_id(value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "granular_permissions.scope blueprint ids must be non-empty strings"
            )
        if " in [" in value or " and " in value or " or " in value:
            raise ValueError(
                "granular_permissions.scope only accepts shorthand blueprint ids, not full expressions"
            )
        return value.strip()

    if isinstance(scope, list):
        if not scope:
            raise ValueError(
                "granular_permissions.scope list must contain at least one blueprint id"
            )
        normalized_scope_values = [_validate_blueprint_id(value) for value in scope]
        quoted_scope = ", ".join(f"'{value}'" for value in normalized_scope_values)
        return f"blueprint_id in [{quoted_scope}]"

    if isinstance(scope, str):
        normalized_scope = _validate_blueprint_id(scope)
        return f"blueprint_id in ['{normalized_scope}']"

    raise ValueError(
        "granular_permissions.scope must be a blueprint id string or list of blueprint ids"
    )


def _normalize_granular_permissions(granular_permissions):
    if not isinstance(granular_permissions, list):
        return granular_permissions

    normalized_permissions = []
    for permission in granular_permissions:
        if not isinstance(permission, dict) or "scope" not in permission:
            normalized_permissions.append(permission)
            continue

        normalized_permission = dict(permission)
        normalized_permission["scope"] = _normalize_blueprint_scope(
            permission.get("scope")
        )
        normalized_permissions.append(normalized_permission)

    return normalized_permissions


def _build_payload(body, current=None):
    payload = {}
    role_name = body.get("role") or body.get("name")
    if role_name:
        payload["role"] = role_name

    if "type" in body and body.get("type") is not None:
        payload["type"] = body.get("type")

    for key in ("label", "description"):
        if key in body:
            payload[key] = body.get(key)

    if "permissions" in body and body.get("permissions") is not None:
        payload["permissions"] = body.get("permissions")

    if "granular_permissions" in body and body.get("granular_permissions") is not None:
        payload["granular_permissions"] = _normalize_granular_permissions(
            body.get("granular_permissions")
        )
    elif (
        "blueprint_permissions" in body
        and body.get("blueprint_permissions") is not None
    ):
        payload["granular_permissions"] = _normalize_granular_permissions(
            body.get("blueprint_permissions")
        )

    if "tenant_permissions" in body and body.get("tenant_permissions") is not None:
        payload["tenant_permissions"] = body.get("tenant_permissions")

    for key, value in body.items():
        if key in (
            "name",
            "role",
            "type",
            "label",
            "description",
            "permissions",
            "global_permissions",
            "granular_permissions",
            "blueprint_permissions",
            "tenant_permissions",
        ):
            continue
        payload[key] = value

    if current:
        for required_key in ("role",):
            if required_key not in payload and required_key in current:
                payload[required_key] = current[required_key]

    return payload


def _compute_changes(current, desired):
    changes = {}
    for key, desired_value in desired.items():
        if key == "id":
            continue
        current_value = current.get(key)
        if not _equal_semantic(current_value, desired_value):
            changes[key] = desired_value
    return changes


def _update_role(base_client, role_id, current, changes):
    # Some Apstra versions reject PATCH on /aaa/roles/{id} with 405.
    # Build a full PUT payload by overlaying desired changes on the current role.
    payload = dict(current)
    payload.update(changes)
    payload.pop("id", None)
    payload.pop("is_role_deletable", None)
    base_client.roles[role_id].update(payload)


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
        state = module.params.get("state")
        id_param = module.params.get("id") or {}

        role_ref = id_param.get("role")
        role_name = body.get("role") or body.get("name")

        if not role_ref and not role_name:
            module.fail_json(
                msg="Either id.role or body.role (or body.name) is required"
            )

        role_id, current = _resolve_role(
            base, factory, role_ref=role_ref, role_name=role_name
        )

        if state == "absent":
            if not current:
                module.exit_json(changed=False, msg="role already absent")

            resolved_role_name = _role_name_from_obj(current) or role_name or role_id
            if resolved_role_name == "administrator":
                module.fail_json(msg="Refusing to delete built-in 'administrator' role")

            if not module.check_mode:
                base.roles[role_id].delete()

            module.exit_json(
                changed=True,
                id={"role": role_id},
                msg=f"role '{resolved_role_name}' deleted",
            )

        # present
        if not body:
            module.fail_json(msg="body is required when state=present")

        role_type = body.get("type")
        if role_type is None:
            module.fail_json(
                msg="body.type is required when state=present (allowed: global, granular)"
            )

        if role_type not in VALID_ROLE_TYPES:
            module.fail_json(
                msg=f"Invalid body.type '{role_type}'. Allowed values: global, granular"
            )

        if not current:
            create_payload = _build_payload(body)
            if "role" not in create_payload:
                module.fail_json(
                    msg="body.role (or body.name) is required to create a role"
                )

            if module.check_mode:
                module.exit_json(
                    changed=True,
                    id={"role": None},
                    msg=f"would create role '{create_payload['role']}'",
                )

            created = base.roles.create(create_payload)
            role_id = created.get("id") if isinstance(created, dict) else None
            final = (
                base.roles[role_id].get()
                if role_id
                else _find_role_by_name(base, create_payload["role"])
            )
            role_id = role_id or (final or {}).get("id")

            module.exit_json(
                changed=True,
                id={"role": role_id},
                role=final,
                msg=f"role '{create_payload['role']}' created",
            )

        desired = _build_payload(body, current=current)
        changes = _compute_changes(current, desired)

        if not changes:
            module.exit_json(
                changed=False,
                id={"role": role_id},
                role=current,
                msg=f"role '{_role_name_from_obj(current) or role_id}' already up to date",
            )

        if module.check_mode:
            module.exit_json(
                changed=True,
                id={"role": role_id},
                role=current,
                changes=changes,
                msg=f"would update role '{_role_name_from_obj(current) or role_id}'",
            )

        _update_role(base, role_id, current, changes)
        final = base.roles[role_id].get()

        module.exit_json(
            changed=True,
            id={"role": role_id},
            role=final,
            changes=changes,
            msg=f"role '{_role_name_from_obj(final) or role_id}' updated",
        )

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"rbac_roles exception: {e}\n{tb}")
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
