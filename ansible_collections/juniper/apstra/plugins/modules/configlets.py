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
module: configlets

short_description: Manage configlets in Apstra

version_added: "0.1.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module allows you to create, update, and delete configlets in Apstra.
  - Supports both catalog (design) configlets and blueprint configlets.
  - Catalog configlets are stored in the global design catalog.
  - Blueprint configlets are applied to a specific blueprint and include a condition for role-based targeting.
  - Configlets contain one or more generators, each specifying the config style (junos, eos, nxos, sonic),
    section (system, set_based_system, interface, set_based_interface, file, ospf, etc.),
    template text, negation template text, and optional filename.

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
  type:
    description:
      - The type of configlet to manage.
      - C(catalog) manages global design configlets at /api/design/configlets.
      - C(blueprint) manages configlets applied to a specific blueprint.
    required: false
    type: str
    choices: ["catalog", "blueprint"]
    default: "catalog"
  id:
    description:
      - Dictionary containing the configlet ID.
      - For catalog configlets, use C(configlet) key.
      - For blueprint configlets, use C(blueprint) and optionally C(configlet) keys.
    required: false
    type: dict
  body:
    description:
      - Dictionary containing the configlet object details.
      - For catalog configlets, keys include C(display_name), C(ref_archs), and C(generators).
      - For blueprint configlets, keys include C(label), C(condition), and C(configlet)
        (which itself contains C(display_name) and C(generators)).
      - Each generator is a dictionary with C(config_style), C(template_text),
        C(negation_template_text), C(section), and C(filename).
    required: false
    type: dict
  state:
    description:
      - Desired state of the configlet.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Create a catalog configlet
  juniper.apstra.configlets:
    type: catalog
    body:
      display_name: "SNMP Config"
      ref_archs:
        - "two_stage_l3clos"
      generators:
        - config_style: "junos"
          section: "system"
          template_text: |
            snmp {
              community public;
            }
          negation_template_text: ""
          filename: ""
    state: present

- name: Update a catalog configlet by display_name
  juniper.apstra.configlets:
    type: catalog
    body:
      display_name: "SNMP Config"
      ref_archs:
        - "two_stage_l3clos"
      generators:
        - config_style: "junos"
          section: "system"
          template_text: |
            snmp {
              community private;
            }
          negation_template_text: ""
          filename: ""
    state: present

- name: Delete a catalog configlet by ID
  juniper.apstra.configlets:
    type: catalog
    id:
      configlet: "550e8400-e29b-41d4-a716-446655440000"
    state: absent

- name: Create a blueprint configlet
  juniper.apstra.configlets:
    type: blueprint
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "Leaf SNMP Config"
      condition: 'role in ["leaf"]'
      configlet:
        display_name: "Leaf SNMP Config"
        generators:
          - config_style: "junos"
            section: "system"
            template_text: |
              snmp {
                community public;
              }
            negation_template_text: ""
            filename: ""
    state: present

- name: Update a blueprint configlet
  juniper.apstra.configlets:
    type: blueprint
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "Leaf SNMP Config"
      condition: 'role in ["leaf", "spine"]'
      configlet:
        display_name: "Leaf SNMP Config"
        generators:
          - config_style: "junos"
            section: "system"
            template_text: |
              snmp {
                community private;
              }
            negation_template_text: ""
            filename: ""
    state: present

- name: Delete a blueprint configlet by ID
  juniper.apstra.configlets:
    type: blueprint
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      configlet: "AjAuUuVLylXCUgAqaQ"
    state: absent

- name: Create a catalog configlet with Jinja2 template variables (NTP)
  juniper.apstra.configlets:
    type: catalog
    body:
      display_name: "NTP Template Config"
      ref_archs:
        - "two_stage_l3clos"
      generators:
        - config_style: "junos"
          section: "system"
          template_text: |
            system {
              ntp {
                server {{ ntp_server }};
                boot-server {{ ntp_server }};
              }
            }
          negation_template_text: ""
          filename: ""
    state: present

- name: Create a multi-vendor AAA catalog configlet (junos, nxos, eos)
  juniper.apstra.configlets:
    type: catalog
    body:
      display_name: "AAA Multi-Vendor Config"
      ref_archs:
        - "two_stage_l3clos"
      generators:
        - config_style: "junos"
          section: "system"
          template_text: |
            system {
              authentication-order [ radius password ];
              radius-server {
                10.0.0.100 secret radpass;
              }
            }
          negation_template_text: ""
          filename: ""
        - config_style: "nxos"
          section: "system"
          template_text: |
            radius-server host 10.0.0.100 key radpass
            aaa authentication login default group radius local
          negation_template_text: ""
          filename: ""
        - config_style: "eos"
          section: "system"
          template_text: |
            radius-server host 10.0.0.100 key radpass
            aaa authentication login default group radius local
          negation_template_text: ""
          filename: ""
    state: present

- name: Create a blueprint syslog configlet
  juniper.apstra.configlets:
    type: blueprint
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "Syslog Config"
      condition: 'role in ["leaf", "spine"]'
      configlet:
        display_name: "Syslog Config"
        generators:
          - config_style: "junos"
            section: "system"
            template_text: |
              system {
                syslog {
                  host 10.0.0.1 {
                    any warning;
                  }
                }
              }
            negation_template_text: ""
            filename: ""
    state: present
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
  description: The configlet object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the configlet.
  returned: on create, or when object identified by display_name/label
  type: dict
  sample: {
      "configlet": "550e8400-e29b-41d4-a716-446655440000"
  }
configlet:
  description: The final configlet object details.
  returned: on create or update
  type: dict
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

# Read-only top-level fields returned by the API for catalog configlets
CATALOG_READ_ONLY_FIELDS = ("id", "created_at", "last_modified_at")

# Read-only fields that the API may add inside generators
GENERATOR_READ_ONLY_FIELDS = ("section_condition", "render_style")


def _strip_read_only_from_generators(obj):
    """Strip read-only fields from generators list so comparison is accurate."""
    generators = obj.get("generators") if isinstance(obj, dict) else None
    if generators and isinstance(generators, list):
        obj["generators"] = [
            {k: v for k, v in gen.items() if k not in GENERATOR_READ_ONLY_FIELDS}
            for gen in generators
        ]


def _strip_read_only_from_blueprint_configlet(obj):
    """Strip read-only fields from a blueprint configlet for comparison."""
    if isinstance(obj, dict) and "configlet" in obj:
        configlet_inner = obj["configlet"]
        _strip_read_only_from_generators(configlet_inner)


def _catalog_find_by_display_name(client_factory, display_name):
    """Find a catalog configlet by display_name."""
    all_items = client_factory.object_request("configlets", "list", {})
    items = []
    if all_items is not None:
        if isinstance(all_items, list):
            items = all_items
        elif isinstance(all_items, dict):
            if "items" in all_items:
                items = all_items["items"]
            elif "id" in all_items:
                items = [all_items]

    for item in items:
        if isinstance(item, dict) and item.get("display_name") == display_name:
            return item
    return None


def _blueprint_list_configlets(client_factory, blueprint_id):
    """List all configlets for a blueprint using raw_request (SDK endpoint is broken)."""
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(f"/blueprints/{blueprint_id}/configlets")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


def _blueprint_get_configlet(client_factory, blueprint_id, configlet_id):
    """Get a single blueprint configlet by ID."""
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}"
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def _blueprint_create_configlet(client_factory, blueprint_id, body):
    """Create a blueprint configlet."""
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets", "POST", data=body
    )
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(
        f"Failed to create blueprint configlet: {resp.status_code} {resp.text}"
    )


def _blueprint_update_configlet(client_factory, blueprint_id, configlet_id, body):
    """Update a blueprint configlet (PUT)."""
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}", "PUT", data=body
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to update blueprint configlet: {resp.status_code} {resp.text}"
        )
    return None


def _blueprint_delete_configlet(client_factory, blueprint_id, configlet_id):
    """Delete a blueprint configlet."""
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}", "DELETE"
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to delete blueprint configlet: {resp.status_code} {resp.text}"
        )


def _blueprint_find_by_label(client_factory, blueprint_id, label):
    """Find a blueprint configlet by label."""
    items = _blueprint_list_configlets(client_factory, blueprint_id)
    for item in items:
        if isinstance(item, dict) and item.get("label") == label:
            return item
    return None


def _manage_catalog_configlet(module, client_factory):
    """Manage a catalog (design) configlet."""
    result = dict(changed=False)

    object_type = "configlets"
    leaf_object_type = singular_leaf_object_type(object_type)

    id = module.params.get("id")
    if id is None:
        id = {}
    body = module.params.get("body", None)
    state = module.params["state"]

    object_id = id.get(leaf_object_type, None)

    # See if the object exists
    current_object = None
    if object_id is None:
        # Try to find by display_name
        display_name = body.get("display_name") if body else None
        if display_name:
            found = _catalog_find_by_display_name(client_factory, display_name)
            if found:
                object_id = found["id"]
                id[leaf_object_type] = object_id
                current_object = found
    else:
        try:
            current_object = client_factory.object_request(object_type, "get", id)
        except Exception as e:
            module.debug(f"Error getting catalog configlet by id: {str(e)}")
            current_object = None

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                # Strip read-only fields before comparison
                _strip_read_only_from_generators(current_object)

                # Strip top-level read-only fields from current for comparison
                compare_current = {
                    k: v
                    for k, v in current_object.items()
                    if k not in CATALOG_READ_ONLY_FIELDS
                }

                changes = {}
                if client_factory.compare_and_update(compare_current, body, changes):
                    # Catalog configlets use PUT (update) and need the full body
                    update_body = {
                        k: v
                        for k, v in current_object.items()
                        if k not in CATALOG_READ_ONLY_FIELDS
                    }
                    updated_object = client_factory.object_request(
                        object_type, "update", id, update_body
                    )
                    result["changed"] = True
                    if updated_object:
                        result["response"] = updated_object
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = f"No changes needed for {leaf_object_type}"
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            created_object = client_factory.object_request(
                object_type, "create", id, body
            )
            if created_object and isinstance(created_object, dict):
                object_id = created_object.get("id")
                if object_id:
                    id[leaf_object_type] = object_id
                    result["id"] = id
                    result["changed"] = True
                    result["response"] = created_object
                    result["msg"] = f"{leaf_object_type} created successfully"
                else:
                    raise ValueError(
                        f"Created object has no 'id' field: {created_object}"
                    )
            else:
                raise ValueError(f"Unexpected create response: {created_object}")

        # Return the final object state
        result[leaf_object_type] = client_factory.object_request(
            object_type=object_type, op="get", id=id, retry=10, retry_delay=3
        )

    if state == "absent":
        if current_object is None:
            result["changed"] = False
            result["msg"] = f"{leaf_object_type} does not exist"
        else:
            if object_id is None:
                raise ValueError(
                    f"Cannot delete a {leaf_object_type} without a configlet id"
                )
            client_factory.object_request(object_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{leaf_object_type} deleted successfully"

    return result


def _manage_blueprint_configlet(module, client_factory):
    """Manage a blueprint configlet using raw HTTP requests (SDK is broken for this endpoint)."""
    result = dict(changed=False)

    id = module.params.get("id")
    if id is None:
        id = {}
    body = module.params.get("body", None)
    state = module.params["state"]

    blueprint_id = id.get("blueprint")
    if not blueprint_id:
        raise ValueError("Must specify 'blueprint' in id for blueprint configlets")

    configlet_id = id.get("configlet", None)

    # See if the object exists
    current_object = None
    if configlet_id is None:
        # Try to find by label
        label = body.get("label") if body else None
        if label:
            found = _blueprint_find_by_label(client_factory, blueprint_id, label)
            if found:
                configlet_id = found["id"]
                id["configlet"] = configlet_id
                current_object = found
    else:
        current_object = _blueprint_get_configlet(
            client_factory, blueprint_id, configlet_id
        )

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                # Strip read-only fields before comparison
                _strip_read_only_from_blueprint_configlet(current_object)

                # Remove 'id' from current for comparison
                compare_current = {k: v for k, v in current_object.items() if k != "id"}

                changes = {}
                if client_factory.compare_and_update(compare_current, body, changes):
                    # Build full update body (without id)
                    update_body = {k: v for k, v in current_object.items() if k != "id"}
                    _blueprint_update_configlet(
                        client_factory, blueprint_id, configlet_id, update_body
                    )
                    result["changed"] = True
                    result["changes"] = changes
                    result["msg"] = "configlet updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = "No changes needed for configlet"
            else:
                result["changed"] = False
                result["msg"] = "No changes specified for configlet"
        else:
            if body is None:
                raise ValueError("Must specify 'body' to create a configlet")
            created = _blueprint_create_configlet(client_factory, blueprint_id, body)
            if created and isinstance(created, dict):
                configlet_id = created.get("id")
                if configlet_id:
                    id["configlet"] = configlet_id
                    result["id"] = id
                    result["changed"] = True
                    result["response"] = created
                    result["msg"] = "configlet created successfully"
                else:
                    raise ValueError(f"Created object has no 'id' field: {created}")
            else:
                raise ValueError(f"Unexpected create response: {created}")

        # Return the final object state (with retry for eventual consistency)
        final_object = None
        for attempt in range(10):
            final_object = _blueprint_get_configlet(
                client_factory, blueprint_id, configlet_id
            )
            if final_object is not None:
                break
            import time

            time.sleep(3)
        result["configlet"] = final_object

    if state == "absent":
        if current_object is None:
            result["changed"] = False
            result["msg"] = "configlet does not exist"
        else:
            if configlet_id is None:
                raise ValueError("Cannot delete a configlet without a configlet id")
            _blueprint_delete_configlet(client_factory, blueprint_id, configlet_id)
            result["changed"] = True
            result["msg"] = "configlet deleted successfully"

    return result


def main():
    object_module_args = dict(
        type=dict(
            type="str",
            required=False,
            choices=["catalog", "blueprint"],
            default="catalog",
        ),
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

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        configlet_type = module.params["type"]

        if configlet_type == "catalog":
            result = _manage_catalog_configlet(module, client_factory)
        elif configlet_type == "blueprint":
            result = _manage_blueprint_configlet(module, client_factory)
        else:
            raise ValueError(f"Unsupported configlet type: {configlet_type}")

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
