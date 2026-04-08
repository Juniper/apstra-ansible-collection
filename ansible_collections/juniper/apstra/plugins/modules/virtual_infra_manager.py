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
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_virtual_infra_manager_id,
)

DOCUMENTATION = """
---
module: virtual_infra_manager

short_description: Manage Virtual Infrastructure Managers in Apstra

version_added: "0.2.0"

author:
  - "Vijay Gavini (@vgavini)"

description:
  - Provides create, read, update and delete operations for Virtual
    Infrastructure Managers (VIMs) in Apstra.
  - Supports two scopes depending on whether C(blueprint) is provided
    in the C(id) parameter.
  - B(Global scope) (no C(blueprint) in C(id)) manages VIM definitions in
    the C(External Systems > Virtual Infra Managers) catalog at
    C(/api/virtual-infra-managers).  These are the connection definitions
    to vCenter, NSX, or Nutanix environments.
  - B(Blueprint scope) (C(blueprint) in C(id)) manages the VIM nodes
    assigned to a specific blueprint at
    C(/api/blueprints/{id}/virtual_infra).  This is where a global VIM
    is linked to a blueprint, specifying C(infra_type) and C(system_id).

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
      - The Apstra username for authentication.
    type: str
    required: false
    default: APSTRA_USERNAME environment variable
  password:
    description:
      - The Apstra password for authentication.
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
      - Dictionary containing identifiers.
      - B(Global scope) — omit C(blueprint).  Use C(virtual_infra_manager)
        (UUID or display_name) for get/update/delete.
      - B(Blueprint scope) — include C(blueprint) (UUID or label).  Use
        C(virtual_infra) (UUID) for get/update/delete an existing node.
    type: dict
    required: false
  body:
    description:
      - Dictionary containing the configuration to create or update.
      - B(Global scope) key fields — C(display_name) (str) human-readable
        name for the VIM; C(type) (str) platform type C(vcenter)/C(nsx)/
        C(nutanix); C(hostname) (str) management IP or hostname;
        C(username) (str) and C(password) (str) login credentials;
        C(port) (int) optional management port.
      - B(Blueprint scope) key fields — C(infra_type) (str) one of
        C(vcenter), C(nsxt), C(nutanix), C(nsx); C(system_id) (str)
        Apstra system identifier; C(agent_id) (str) optional agent ID.
    type: dict
    required: false
  state:
    description:
      - Desired state.
      - C(present) — create or update.
      - C(absent) — delete.
    type: str
    required: false
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Global scope: create a vCenter VIM ───────────────────────────

- name: Create global vCenter VIM
  juniper.apstra.virtual_infra_manager:
    body:
      display_name: "prod-vcenter"
      type: "vcenter"
      hostname: "vcenter.example.com"
      username: "administrator@vsphere.local"
      password: "S3cret!"
    state: present
  register: vim_result

- name: Show created VIM ID
  ansible.builtin.debug:
    var: vim_result.id.virtual_infra_manager

# ── Global scope: update by display_name ─────────────────────────

- name: Update VIM hostname by display_name (auto-resolved to ID)
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "prod-vcenter"   # display_name works
    body:
      hostname: "vcenter2.example.com"
    state: present

# ── Global scope: update by UUID ─────────────────────────────────

- name: Update VIM by UUID
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
    body:
      hostname: "vcenter2.example.com"
    state: present

# ── Global scope: delete ─────────────────────────────────────────

- name: Delete global VIM by UUID
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
    state: absent

- name: Delete global VIM by display_name
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "prod-vcenter"
    state: absent

# ── Blueprint scope: assign VIM node to a blueprint ──────────────

- name: Add virtual infra node to blueprint
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"   # name or UUID
    body:
      infra_type: "vcenter"
      system_id: "{{ vcenter_system_id }}"
    state: present
  register: bp_vim

# ── Blueprint scope: update VIM node ─────────────────────────────

- name: Update blueprint VIM node
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
      virtual_infra: "{{ bp_vim.id.virtual_infra }}"
    body:
      infra_type: "nsx"
    state: present

# ── Blueprint scope: remove VIM node ─────────────────────────────

- name: Remove virtual infra node from blueprint
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
      virtual_infra: "{{ bp_vim.id.virtual_infra }}"
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module made any changes.
  type: bool
  returned: always
id:
  description: >
    The resolved ID dictionary for the created or targeted object.
    For global scope: contains C(virtual_infra_manager) key.
    For blueprint scope: contains C(blueprint) and C(virtual_infra) keys.
  type: dict
  returned: on create or when object identified by name
  sample:
    virtual_infra_manager: "a1b2c3d4-..."
response:
  description: The full API response object returned on create or patch.
  type: dict
  returned: on create or update
virtual_infra_manager:
  description: The VIM object details (global scope).
  type: dict
  returned: on present (global scope)
virtual_infra:
  description: The blueprint VIM node details (blueprint scope).
  type: dict
  returned: on present (blueprint scope)
changes:
  description: Dictionary of fields that were updated.
  type: dict
  returned: on update
msg:
  description: Human-readable status message.
  type: str
  returned: always
"""


# ──────────────────────────────────────────────────────────────────
#  Global scope handler
# ──────────────────────────────────────────────────────────────────


def _handle_global_vim(module, client_factory, id, body, state, result):
    """Handle global VIM CRUD at /api/virtual-infra-managers."""
    object_type = "virtual_infra_managers"
    leaf_object_type = "virtual_infra_manager"  # singular per framework

    object_id = id.get(leaf_object_type) if id else None

    # Resolve display_name → UUID if needed
    if object_id:
        object_id = resolve_virtual_infra_manager_id(client_factory, object_id)
        id[leaf_object_type] = object_id

    # Look up existing object
    current_object = None
    if object_id is not None:
        current_object = client_factory.object_request(object_type, "get", id)
    elif body and body.get("display_name"):
        # Search by display_name in the list
        all_vims = client_factory.object_request(object_type, "get", {})
        if isinstance(all_vims, list):
            for vim in all_vims:
                if vim.get("display_name") == body["display_name"]:
                    current_object = vim
                    if id is None:
                        id = {}
                    id[leaf_object_type] = vim["id"]
                    break

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                changes = {}
                if client_factory.compare_and_update(current_object, body, changes):
                    updated = client_factory.object_request(
                        object_type, "patch", id, changes
                    )
                    result["changed"] = True
                    if updated:
                        result["response"] = updated
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = (
                        f"{leaf_object_type} already exists, no changes needed"
                    )
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            created = client_factory.object_request(object_type, "create", {}, body)
            if isinstance(created, dict) and "id" in created:
                if id is None:
                    id = {}
                id[leaf_object_type] = created["id"]
            result["id"] = id
            result["changed"] = True
            result["response"] = created
            result["msg"] = f"{leaf_object_type} created successfully"

        # Return final object state
        if current_object is not None:
            result[leaf_object_type] = current_object
        elif id and id.get(leaf_object_type):
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type,
                op="get",
                id=id,
                retry=10,
                retry_delay=3,
            )

    elif state == "absent":
        if id is None or leaf_object_type not in id:
            raise ValueError(
                f"Must specify '{leaf_object_type}' in id "
                "(UUID or display_name) to delete"
            )
        client_factory.object_request(object_type, "delete", id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


# ──────────────────────────────────────────────────────────────────
#  Blueprint scope handler
# ──────────────────────────────────────────────────────────────────


def _handle_blueprint_vim(module, client_factory, id, body, state, result):
    """Handle blueprint-level VIM CRUD at /api/blueprints/{id}/virtual_infra."""
    object_type = "blueprints.virtual_infra"
    leaf_object_type = singular_leaf_object_type(object_type)  # "virtual_infra"

    object_id = id.get(leaf_object_type)

    # Look up existing object
    current_object = None
    if object_id is not None:
        current_object = client_factory.object_request(object_type, "get", id)
    elif body and body.get("system_id"):
        # Search by system_id in the list
        all_vims = client_factory.object_request(
            object_type, "get", {k: v for k, v in id.items() if k != leaf_object_type}
        )
        if isinstance(all_vims, list):
            for vim in all_vims:
                if vim.get("system_id") == body["system_id"]:
                    current_object = vim
                    id[leaf_object_type] = vim["id"]
                    break

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                changes = {}
                if client_factory.compare_and_update(current_object, body, changes):
                    updated = client_factory.object_request(
                        object_type, "patch", id, changes
                    )
                    result["changed"] = True
                    if updated:
                        result["response"] = updated
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = (
                        f"{leaf_object_type} already exists, no changes needed"
                    )
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            created = client_factory.object_request(object_type, "create", id, body)
            if isinstance(created, dict) and "id" in created:
                id[leaf_object_type] = created["id"]
            result["id"] = id
            result["changed"] = True
            result["response"] = created
            result["msg"] = f"{leaf_object_type} created successfully"

        # Return final object state
        if current_object is not None:
            result[leaf_object_type] = current_object
        elif id.get(leaf_object_type):
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type,
                op="get",
                id=id,
                retry=10,
                retry_delay=3,
            )

    elif state == "absent":
        if leaf_object_type not in id:
            raise ValueError(f"Must specify '{leaf_object_type}' in id to delete")
        client_factory.object_request(object_type, "delete", id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False, default=None),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        id = dict(module.params.get("id") or {})
        body = module.params.get("body")
        state = module.params["state"]

        # Resolve blueprint name → ID if present
        if "blueprint" in id:
            id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])

        is_blueprint_scope = "blueprint" in id

        if is_blueprint_scope:
            _handle_blueprint_vim(module, client_factory, id, body, state, result)
        else:
            _handle_global_vim(module, client_factory, id, body, state, result)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
