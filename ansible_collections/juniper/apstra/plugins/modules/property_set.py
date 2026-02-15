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
module: property_set
short_description: Manage property sets in Apstra
version_added: "0.1.0"
author:
  - "Juniper Networks"
description:
  - This module allows you to create, update, and delete property sets
    in Apstra.
  - Supports two scopes depending on whether C(blueprint) is provided
    in the C(id) parameter.
  - B(Global scope) (no C(blueprint) in C(id)) manages property sets in
    the Design > Property Sets catalog at C(/api/property-sets).  Specify
    C(label) and C(values) (dict) in C(body) to create; C(property_set)
    in C(id) to get/update/delete.
  - B(Blueprint scope) (C(blueprint) in C(id)) manages property sets
    assigned to a specific blueprint.
  - For Datacenter (two_stage_l3clos) designs, property sets are imported
    from the global catalog into a blueprint by specifying the global
    property set C(id) (and optionally a list of C(keys) for partial import).
  - For Freeform designs, property sets are created directly within the
    blueprint by specifying C(label) and C(values) (or C(values_yaml)).
  - Property sets allow arbitrary key-value context to be passed to Jinja
    templates for configuration rendering.
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
      - Dictionary containing identifiers for the property set.
      - For global property sets (Design catalog), omit C(blueprint) and
        use C(property_set) for get/update/delete.
      - For blueprint-scoped property sets, include C(blueprint) and
        optionally C(property_set).
    required: false
    type: dict
  body:
    description:
      - Dictionary containing the property set details.
      - For global property sets, use C(label) and either C(values) (dict)
        or C(values_yaml) (YAML string) to create.  Use C(values) or
        C(values_yaml) to update.  The two fields are alternatives;
        provide one or the other.
      - For Datacenter blueprint import, use C(id) (global property set id)
        and optionally C(keys) (list of keys for partial import).
      - For Freeform blueprints, use C(label), C(values) (dict) or
        C(values_yaml) (YAML string), and optionally C(system_id).
      - The API always returns both C(values) and C(values_yaml) in
        responses regardless of which was used to create/update.
    required: false
    type: dict
  state:
    description:
      - Desired state of the property set.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# Global scope -- create a new property set in the Design catalog
- name: Create global property set
  juniper.apstra.property_set:
    body:
      label: "my_custom_ps"
      values:
        ntp_server: "10.0.0.1"
        mtu: 9100
    state: present
  register: global_ps

# Global scope -- update a property set
- name: Update global property set
  juniper.apstra.property_set:
    id:
      property_set: "{{ global_ps.id.property_set }}"
    body:
      values:
        ntp_server: "10.0.0.2"
        mtu: 9200
    state: present

# Global scope -- create using values_yaml key inside values dict
- name: Create global property set with values_yaml as a key in values
  juniper.apstra.property_set:
    body:
      label: "my_ps_with_yaml_key"
      values:
        ntp_server: "10.0.0.1"
        values_yaml: "mtu: 9100\nospf_area: 0.0.0.0\n"
    state: present

# Global scope -- create using values_yaml (YAML string)
- name: Create global property set with YAML string values
  juniper.apstra.property_set:
    body:
      label: "my_yaml_ps"
      values_yaml: |
        ntp_server: 10.0.0.1
        mtu: 9100
    state: present
  register: yaml_ps

# Global scope -- update using values_yaml
- name: Update global property set with YAML string
  juniper.apstra.property_set:
    id:
      property_set: "{{ yaml_ps.id.property_set }}"
    body:
      values_yaml: |
        ntp_server: 10.0.0.2
        mtu: 9200
    state: present

# Global scope -- delete a property set
- name: Delete global property set
  juniper.apstra.property_set:
    id:
      property_set: "{{ global_ps.id.property_set }}"
    state: absent

# Blueprint scope -- import a global property set into a blueprint
- name: Import global property set into blueprint
  juniper.apstra.property_set:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      id: "dcqcn"
    state: present

# Blueprint scope -- partial import with specific keys
- name: Import property set with specific keys
  juniper.apstra.property_set:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      id: "dcqcn"
      keys:
        - "dcqcn"
    state: present

# Blueprint scope -- Freeform design, create directly
- name: Create property set in freeform blueprint
  juniper.apstra.property_set:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "my_property_set"
      values:
        mtu: 9100
        ntp_server: "10.0.0.1"
    state: present

# Blueprint scope -- Freeform design, create using values_yaml
- name: Create property set in freeform blueprint with YAML string
  juniper.apstra.property_set:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "my_yaml_property_set"
      values_yaml: |
        mtu: 9100
        ntp_server: 10.0.0.1
    state: present

# Blueprint scope -- Freeform design, update using values_yaml
- name: Update property set in freeform blueprint with YAML string
  juniper.apstra.property_set:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      property_set: "abc-123"
    body:
      values_yaml: |
        mtu: 9200
        ntp_server: 10.0.0.2
    state: present

# Blueprint scope -- delete a property set
- name: Delete property set from blueprint
  juniper.apstra.property_set:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      property_set: "abc-123"
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
  description: The property set object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the property set.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "property_set": "dcqcn"
  }
property_set:
  description: The property set object details.
  type: dict
  returned: on create or update
  sample: {
      "id": "dcqcn",
      "label": "DataCenter QoS Congestion Notification",
      "values": {"dcqcn": {"drop_profile": {}}}
  }
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


def _handle_global_property_set(module, client_factory, id, body, state, result):
    """
    Handle global property sets (Design > Property Sets catalog).
    Object type: property_sets (no blueprint prefix).
    """
    object_type = "property_sets"
    leaf_object_type = "property_set"

    object_id = id.get(leaf_object_type, None) if id else None

    # Look up existing object
    current_object = None
    if object_id is not None:
        current_object = client_factory.object_request(object_type, "get", id)
    elif body and "label" in body:
        # Search by label in the list
        all_ps = client_factory.object_request(object_type, "get", {})
        if isinstance(all_ps, list):
            for ps in all_ps:
                if ps.get("label") == body["label"]:
                    current_object = ps
                    if id is None:
                        id = {}
                    id[leaf_object_type] = ps["id"]
                    break

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
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

        # Return the final object state
        if id and id.get(leaf_object_type):
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type,
                op="get",
                id=id,
                retry=10,
                retry_delay=3,
            )

    elif state == "absent":
        if id is None or leaf_object_type not in id:
            raise ValueError(f"Must specify '{leaf_object_type}' in id to delete")
        client_factory.object_request(object_type, "delete", id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


def _handle_blueprint_property_set(module, client_factory, id, body, state, result):
    """
    Handle blueprint-scoped property sets.
    Object type: blueprints.property_sets
    """
    object_type = "blueprints.property_sets"
    leaf_object_type = singular_leaf_object_type(object_type)

    # Validate the id
    missing_id = client_factory.validate_id(object_type, id)
    if len(missing_id) > 1 or (
        len(missing_id) == 1 and state == "absent" and missing_id[0] != leaf_object_type
    ):
        raise ValueError(f"Invalid id: {id} for desired state of {state}.")
    object_id = id.get(leaf_object_type, None)

    # See if the object exists
    current_object = None
    if object_id is None:
        if (body is not None) and ("id" in body):
            # Datacenter import: check if the global property set is
            # already imported into the blueprint using body["id"].
            try:
                check_id = dict(id)
                check_id[leaf_object_type] = body["id"]
                current_object = client_factory.object_request(
                    object_type, "get", check_id
                )
                if current_object:
                    id[leaf_object_type] = body["id"]
            except Exception:
                current_object = None
        elif (body is not None) and ("label" in body):
            # Freeform design: look up by label
            id_found = client_factory.get_id_by_label(
                id["blueprint"], leaf_object_type, body["label"]
            )
            if id_found:
                id[leaf_object_type] = id_found
                current_object = client_factory.object_request(object_type, "get", id)
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
                    result["msg"] = (
                        f"{leaf_object_type} already exists, no changes needed"
                    )
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            # Create the object
            created = client_factory.object_request(object_type, "create", id, body)
            if isinstance(created, dict) and "id" in created:
                object_id = created["id"]
                id[leaf_object_type] = object_id
            result["id"] = id
            result["changed"] = True
            result["response"] = created
            result["msg"] = f"{leaf_object_type} created successfully"

        # Return the final object state (may take a few tries)
        if id.get(leaf_object_type):
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type,
                op="get",
                id=id,
                retry=10,
                retry_delay=3,
            )

    if state == "absent":
        if leaf_object_type not in id:
            raise ValueError(f"Must specify '{leaf_object_type}' in id to delete")
        client_factory.object_request(object_type, "delete", id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


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

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        # Validate params
        id = module.params.get("id", None) or {}
        body = module.params.get("body", None)
        state = module.params["state"]

        # Determine scope: global vs blueprint
        is_blueprint_scope = "blueprint" in id

        if is_blueprint_scope:
            _handle_blueprint_property_set(
                module, client_factory, id, body, state, result
            )
        else:
            _handle_global_property_set(module, client_factory, id, body, state, result)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
