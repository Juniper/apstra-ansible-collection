#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import traceback
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

DOCUMENTATION = """
---
module: generic_systems

short_description: Manage generic systems in Apstra blueprints

version_added: "0.1.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module allows you to create, update, and delete generic systems in Apstra blueprints.
  - Generic systems represent servers, storage devices, or other endpoints connected
    to leaf switches in a blueprint.
  - Uses the C(switch-system-links) API to create generic systems with their links to switches.
  - Also supports external generic systems (outside of racks) via the
    C(external-generic-systems) API.
  - Supports updating generic system properties such as hostname, label, deploy mode.
  - Supports deleting generic systems by removing all their switch-system links
    (removing the last link deletes the system) or by direct deletion for external systems.
  - Requires a blueprint to already exist and leaf switches to have interface maps
    assigned before creating generic systems.

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
      - Dictionary containing the IDs for the generic system.
      - C(blueprint) is always required and specifies the blueprint ID.
      - C(generic_system) is the system node ID within the blueprint, required for
        update and delete operations.
    required: false
    type: dict
  body:
    description:
      - Dictionary containing the generic system configuration.
      - For creating a new generic system, provide C(links) and C(new_systems).
      - C(links) is a list of link definitions connecting switches to the system.
        Each link requires C(switch) (with C(system_id), C(transformation_id), C(if_name)),
        C(system) (with C(system_id) set to null for new systems), and optionally
        C(lag_mode), C(link_group_label), C(new_system_index), C(tags).
      - C(new_systems) is a list of new system definitions. Each requires C(system_type),
        C(label), C(hostname), C(deploy_mode), and C(logical_device) (with C(id),
        C(display_name), C(panels)).
      - For updating an existing system, provide C(hostname), C(label), C(deploy_mode)
        at the top level and set C(id.generic_system) to the system node ID.
      - For external generic systems, set C(external) to true.
    required: false
    type: dict
  state:
    description:
      - Desired state of the generic system.
      - C(present) will create or update the generic system.
      - C(absent) will delete the generic system by removing all its links
        (for in-rack systems) or via direct deletion (for external systems).
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Create a Generic System ────────────────────────────────────────
# Creates a new generic system (server) connected to a leaf switch.
# The switch-system-links API creates both the link and the new system.
# The leaf switch must have an interface map assigned.

- name: Create a generic system with a link to a leaf switch
  juniper.apstra.generic_systems:
    id:
      blueprint: "{{ bp_id }}"
    body:
      links:
        - lag_mode: null
          switch:
            system_id: "{{ leaf_id }}"
            transformation_id: 1
            if_name: "xe-0/0/7"
          system:
            system_id: null
          new_system_index: 0
      new_systems:
        - system_type: "server"
          hostname: "my-server-01"
          label: "my-server-01"
          deploy_mode: "deploy"
          logical_device:
            id: "AOS-1x10-1"
            display_name: "AOS-1x10-1"
            panels:
              - port_groups:
                  - roles:
                      - "leaf"
                      - "access"
                    count: 1
                    speed:
                      value: 10
                      unit: "G"
                port_indexing:
                  schema: "absolute"
                  order: "T-B, L-R"
                  start_index: 1
                panel_layout:
                  row_count: 1
                  column_count: 1
          port_channel_id_min: 0
          port_channel_id_max: 0
    state: present

# ── Create a Generic System with LAG ───────────────────────────────

- name: Create a generic system with dual LAG links
  juniper.apstra.generic_systems:
    id:
      blueprint: "{{ bp_id }}"
    body:
      links:
        - lag_mode: "lacp_active"
          link_group_label: "server-lag"
          switch:
            system_id: "{{ leaf_id }}"
            transformation_id: 1
            if_name: "xe-0/0/6"
          system:
            system_id: null
          new_system_index: 0
        - lag_mode: "lacp_active"
          link_group_label: "server-lag"
          switch:
            system_id: "{{ leaf_id }}"
            transformation_id: 1
            if_name: "xe-0/0/7"
          system:
            system_id: null
          new_system_index: 0
      new_systems:
        - system_type: "server"
          hostname: "my-lag-server"
          label: "my-lag-server"
          deploy_mode: "deploy"
          logical_device:
            id: "AOS-2x10-1"
            display_name: "AOS-2x10-1"
            panels:
              - port_groups:
                  - roles:
                      - "leaf"
                      - "access"
                    count: 2
                    speed:
                      value: 10
                      unit: "G"
                port_indexing:
                  schema: "absolute"
                  order: "T-B, L-R"
                  start_index: 1
                panel_layout:
                  row_count: 1
                  column_count: 2
          port_channel_id_min: 0
          port_channel_id_max: 0
    state: present

# ── Update a Generic System ────────────────────────────────────────

- name: Update generic system hostname and deploy mode
  juniper.apstra.generic_systems:
    id:
      blueprint: "{{ bp_id }}"
      generic_system: "{{ generic_system_id }}"
    body:
      hostname: "my-server-01-updated"
      label: "my-server-01-updated"
    state: present

# ── Add a Link to Existing Generic System ──────────────────────────

- name: Add another link to existing generic system
  juniper.apstra.generic_systems:
    id:
      blueprint: "{{ bp_id }}"
    body:
      links:
        - switch:
            system_id: "{{ leaf_id }}"
            transformation_id: 1
            if_name: "xe-0/0/8"
          system:
            system_id: "{{ generic_system_id }}"
    state: present

# ── Delete a Generic System ────────────────────────────────────────
# Removing all links to a generic system will remove the system itself.

- name: Delete a generic system
  juniper.apstra.generic_systems:
    id:
      blueprint: "{{ bp_id }}"
      generic_system: "{{ generic_system_id }}"
    state: absent

# ── Create External Generic System ─────────────────────────────────
# External generic systems are systems outside of racks.

- name: Create external generic system
  juniper.apstra.generic_systems:
    id:
      blueprint: "{{ bp_id }}"
    body:
      external: true
      hostname: "external-server-01"
      label: "external-server-01"
    state: present

# ── Delete External Generic System ─────────────────────────────────

- name: Delete external generic system
  juniper.apstra.generic_systems:
    id:
      blueprint: "{{ bp_id }}"
      generic_system: "{{ ext_system_id }}"
    body:
      external: true
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
id:
  description: The IDs of the generic system.
  returned: on create or when identified
  type: dict
  sample: {
      "blueprint": "e979c23f-c567-48ea-92fb-10718fb84475",
      "generic_system": "AbCdEfGhIjKlMn"
  }
response:
  description: The API response from the create operation.
  type: dict
  returned: when state is present and a system is created
generic_system:
  description: The final generic system object details.
  returned: on create or update
  type: dict
links:
  description: List of link IDs created by the switch-system-links API.
  returned: on create via switch-system-links
  type: list
changes:
  description: Dictionary of changes made during an update.
  returned: on update when changes are made
  type: dict
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

# Read-only fields returned by /nodes/{id} that should not be compared for changes
GENERIC_SYSTEM_READ_ONLY_FIELDS = (
    "id",
    "type",
    "system_id",
    "system_type",
    "management_level",
    "external",
    "role",
    "system_index",
    "position_data",
    "property_set",
    "user_data",
    "group_label",
    "tags",
    "access_l3_peer_link_port_channel_id_min",
    "access_l3_peer_link_port_channel_id_max",
)


# ──────────────────────────────────────────────────────────────────
#  Low-level API helpers
# ──────────────────────────────────────────────────────────────────


def _list_generic_systems(client_factory, blueprint_id):
    """List all generic systems (system_type=server) in a blueprint using QE."""
    base_client = client_factory.get_base_client()
    query_payload = {"query": "node('system', system_type='server', name='gs')"}
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/qe",
        "POST",
        data=query_payload,
    )
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        return [item.get("gs", item) for item in items if isinstance(item, dict)]
    return []


def _get_generic_system(client_factory, blueprint_id, system_id):
    """Get a single system node by its ID.

    Uses GET /api/blueprints/{blueprint_id}/nodes/{system_id}
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(f"/blueprints/{blueprint_id}/nodes/{system_id}")
    if resp.status_code == 200:
        return resp.json()
    return None


def _find_generic_system_by_label(client_factory, blueprint_id, label):
    """Find a generic system by label using the QE."""
    base_client = client_factory.get_base_client()
    query_payload = {
        "query": f"node('system', system_type='server', label='{label}', name='gs')"
    }
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/qe",
        "POST",
        data=query_payload,
    )
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        if items:
            return items[0].get("gs", items[0])
    return None


def _create_switch_system_links(client_factory, blueprint_id, body):
    """Create switch-system links (and optionally new systems).

    POST /api/blueprints/{blueprint_id}/switch-system-links

    Returns dict with 'ids' (list of created link IDs).
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/switch-system-links",
        "POST",
        data=body,
    )
    if resp.status_code in (200, 201):
        try:
            return resp.json()
        except Exception:
            return {"ids": []}
    raise Exception(
        f"Failed to create switch-system-links: {resp.status_code} {resp.text}"
    )


def _delete_switch_system_links(client_factory, blueprint_id, link_ids):
    """Delete switch-system links.

    POST /api/blueprints/{blueprint_id}/delete-switch-system-links

    Removing the last link towards a system leads to the system removal.
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/delete-switch-system-links",
        "POST",
        data={"link_ids": link_ids},
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"Failed to delete switch-system-links: {resp.status_code} {resp.text}"
        )


def _get_system_link_ids(client_factory, blueprint_id, system_id):
    """Get all link IDs connected to a system node using QE.

    Traverses: system -> hosted_interfaces -> interface -> link -> link node
    """
    base_client = client_factory.get_base_client()
    query_payload = {
        "query": (
            f"node('system', id='{system_id}', name='gs')"
            f".out('hosted_interfaces').node('interface', name='intf')"
            f".out('link').node('link', name='link')"
        )
    }
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/qe",
        "POST",
        data=query_payload,
    )
    if resp.status_code == 200:
        data = resp.json()
        link_ids = set()
        for item in data.get("items", []):
            if isinstance(item, dict):
                link_info = item.get("link", {})
                if isinstance(link_info, dict) and link_info.get("id"):
                    # Only include physical links (ethernet), not aggregate_link (LAG)
                    # The delete-switch-system-links API rejects non-physical links
                    if link_info.get("link_type") != "aggregate_link":
                        link_ids.add(link_info["id"])
        return list(link_ids)
    return []


def _update_generic_system(client_factory, blueprint_id, system_id, body):
    """Update a generic system's properties via PATCH.

    PATCH /api/blueprints/{blueprint_id}/nodes/{system_id}
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/nodes/{system_id}",
        "PATCH",
        data=body,
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to update generic system: {resp.status_code} {resp.text}"
        )
    try:
        return resp.json()
    except Exception:
        return None


def _create_external_generic_system(client_factory, blueprint_id, body):
    """Create an external generic system (outside of racks).

    POST /api/blueprints/{blueprint_id}/external-generic-systems
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/external-generic-systems",
        "POST",
        data=body,
    )
    if resp.status_code in (200, 201, 202):
        try:
            return resp.json()
        except Exception:
            return {"id": None}
    raise Exception(
        f"Failed to create external generic system: {resp.status_code} {resp.text}"
    )


def _delete_external_generic_system(client_factory, blueprint_id, system_id):
    """Delete an external generic system.

    DELETE /api/blueprints/{blueprint_id}/external-generic-systems/{system_id}
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/external-generic-systems/{system_id}",
        "DELETE",
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to delete external generic system: {resp.status_code} {resp.text}"
        )


# ──────────────────────────────────────────────────────────────────
#  State management (present / absent)
# ──────────────────────────────────────────────────────────────────


def _manage_generic_system(module, client_factory):
    """Top-level dispatcher for managing a generic system."""
    result = dict(changed=False)

    id_param = module.params.get("id")
    if id_param is None:
        id_param = {}
    body = module.params.get("body", None)
    state = module.params["state"]

    blueprint_id = id_param.get("blueprint")
    if not blueprint_id:
        raise ValueError("Must specify 'blueprint' in id for generic systems")

    system_id = id_param.get("generic_system", None)
    is_external = body.get("external", False) if body else False

    if state == "present":
        if is_external:
            result = _handle_external_present(
                module, client_factory, id_param, blueprint_id, system_id, body
            )
        elif system_id and body and not body.get("links"):
            # Update existing generic system properties
            result = _handle_update(
                module, client_factory, id_param, blueprint_id, system_id, body
            )
        elif body and body.get("links") is not None:
            # Create via switch-system-links (may create new systems or add links)
            result = _handle_create_with_links(
                module, client_factory, id_param, blueprint_id, system_id, body
            )
        elif system_id:
            # Just fetch and return existing system
            current = _get_generic_system(client_factory, blueprint_id, system_id)
            if current:
                result["changed"] = False
                result["id"] = id_param
                result["generic_system"] = current
                result["msg"] = "generic system already exists"
            else:
                raise ValueError(
                    f"Generic system '{system_id}' not found in "
                    f"blueprint '{blueprint_id}'"
                )
        else:
            raise ValueError(
                "Must specify 'body' with 'links' and 'new_systems' to create "
                "a generic system, or 'id.generic_system' with properties to update"
            )

    elif state == "absent":
        result = _handle_absent(
            module, client_factory, id_param, blueprint_id, system_id, body, is_external
        )

    return result


# ── Present: Create via switch-system-links ────────────────────────


def _handle_create_with_links(
    module, client_factory, id_param, blueprint_id, system_id, body
):
    """Create a generic system by posting to switch-system-links."""
    result = dict(changed=False)

    # Idempotency: check if a system with this label already exists
    new_systems = body.get("new_systems", [])
    if new_systems and not system_id:
        for ns in new_systems:
            label = ns.get("label")
            if label:
                found = _find_generic_system_by_label(
                    client_factory, blueprint_id, label
                )
                if found:
                    system_id = found.get("id")
                    id_param["generic_system"] = system_id
                    result["id"] = id_param
                    result["changed"] = False
                    result["generic_system"] = found
                    result["msg"] = "generic system already exists"
                    return result

    # Build the API payload
    api_body = {}
    if "links" in body:
        api_body["links"] = body["links"]
    if "new_systems" in body:
        api_body["new_systems"] = body["new_systems"]

    # Call the switch-system-links API
    created = _create_switch_system_links(client_factory, blueprint_id, api_body)

    result["changed"] = True
    result["response"] = created
    result["links"] = created.get("ids", [])

    # Try to identify the newly created system
    if new_systems:
        label = new_systems[0].get("label") or new_systems[0].get("hostname")
        if label:
            found = None
            for _attempt in range(10):
                found = _find_generic_system_by_label(
                    client_factory, blueprint_id, label
                )
                if found:
                    break
                time.sleep(1)
            if found:
                system_id = found.get("id")
                id_param["generic_system"] = system_id
                result["generic_system"] = found

    result["id"] = id_param
    result["msg"] = "generic system created successfully"
    return result


# ── Present: Update existing system ────────────────────────────────


def _handle_update(module, client_factory, id_param, blueprint_id, system_id, body):
    """Update an existing generic system's properties."""
    result = dict(changed=False)

    current = _get_generic_system(client_factory, blueprint_id, system_id)
    if current is None:
        raise ValueError(
            f"Generic system '{system_id}' not found in blueprint '{blueprint_id}'"
        )

    result["id"] = id_param

    # Strip read-only fields for comparison
    update_body = {
        k: v
        for k, v in body.items()
        if k not in GENERIC_SYSTEM_READ_ONLY_FIELDS and k != "external"
    }
    compare_current = {
        k: v for k, v in current.items() if k not in GENERIC_SYSTEM_READ_ONLY_FIELDS
    }

    changes = {}
    if client_factory.compare_and_update(compare_current, update_body, changes):
        _update_generic_system(client_factory, blueprint_id, system_id, update_body)
        result["changed"] = True
        result["changes"] = changes
        result["msg"] = "generic system updated successfully"
    else:
        result["changed"] = False
        result["msg"] = "No changes needed for generic system"

    # Fetch final state (PATCH returns 202 async, so wait for propagation)
    if result["changed"]:
        time.sleep(1)
    final = _get_generic_system(client_factory, blueprint_id, system_id)
    result["generic_system"] = final
    return result


# ── Present: External generic system ──────────────────────────────


def _handle_external_present(
    module, client_factory, id_param, blueprint_id, system_id, body
):
    """Handle present state for external generic systems."""
    result = dict(changed=False)

    # Strip the 'external' flag from body before sending to API
    api_body = {k: v for k, v in body.items() if k != "external"}

    if system_id:
        # Update existing external generic system
        current = _get_generic_system(client_factory, blueprint_id, system_id)
        if current:
            changes = {}
            compare_current = {
                k: v
                for k, v in current.items()
                if k not in GENERIC_SYSTEM_READ_ONLY_FIELDS
            }
            if client_factory.compare_and_update(compare_current, api_body, changes):
                _update_generic_system(
                    client_factory, blueprint_id, system_id, api_body
                )
                result["changed"] = True
                result["changes"] = changes
                result["msg"] = "external generic system updated successfully"
            else:
                result["changed"] = False
                result["msg"] = "No changes needed for external generic system"
            result["id"] = id_param
            # Re-fetch final state after update (PATCH is async 202)
            if result["changed"]:
                time.sleep(1)
            final = _get_generic_system(client_factory, blueprint_id, system_id)
            result["generic_system"] = final
            return result
        else:
            raise ValueError(
                f"External generic system '{system_id}' not found in "
                f"blueprint '{blueprint_id}'"
            )
    else:
        # Idempotency: check if a system with this label already exists
        label = api_body.get("label")
        if label:
            found = _find_generic_system_by_label(client_factory, blueprint_id, label)
            if found:
                system_id = found.get("id")
                id_param["generic_system"] = system_id
                result["id"] = id_param
                result["changed"] = False
                result["generic_system"] = found
                result["msg"] = "external generic system already exists"
                return result

        # Create new external generic system
        created = _create_external_generic_system(
            client_factory, blueprint_id, api_body
        )
        if created and isinstance(created, dict):
            new_id = created.get("id")
            if new_id:
                system_id = new_id
                id_param["generic_system"] = new_id
        result["id"] = id_param
        result["changed"] = True
        result["response"] = created
        result["msg"] = "external generic system created successfully"

    # Fetch final state
    if system_id:
        final = None
        for _attempt in range(5):
            final = _get_generic_system(client_factory, blueprint_id, system_id)
            if final is not None:
                break
            time.sleep(1)
        result["generic_system"] = final

    return result


# ── Absent: Delete ─────────────────────────────────────────────────


def _handle_absent(
    module, client_factory, id_param, blueprint_id, system_id, body, is_external
):
    """Handle absent state – delete a generic system."""
    result = dict(changed=False)

    # Try to find system by label if no system_id given
    if not system_id:
        label = body.get("label") if body else None
        if label:
            found = _find_generic_system_by_label(client_factory, blueprint_id, label)
            if found:
                system_id = found.get("id")
                id_param["generic_system"] = system_id
                if not is_external and found.get("external"):
                    is_external = True

    if not system_id:
        result["changed"] = False
        result["msg"] = "generic system does not exist"
        return result

    # Check if system still exists
    current = _get_generic_system(client_factory, blueprint_id, system_id)
    if current is None:
        result["changed"] = False
        result["msg"] = "generic system does not exist"
        return result

    if is_external or current.get("external"):
        # Delete external generic system directly
        _delete_external_generic_system(client_factory, blueprint_id, system_id)
        result["changed"] = True
        result["msg"] = "external generic system deleted successfully"
    else:
        # Find all links and delete them (removing last link removes system)
        link_ids = _get_system_link_ids(client_factory, blueprint_id, system_id)
        if link_ids:
            _delete_switch_system_links(client_factory, blueprint_id, link_ids)
            result["changed"] = True
            result["msg"] = "generic system deleted successfully (all links removed)"
        else:
            result["changed"] = False
            result["msg"] = (
                "generic system has no links to remove. "
                "For external generic systems set body.external=true."
            )

    return result


# ──────────────────────────────────────────────────────────────────
#  Entry point
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

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)
        result = _manage_generic_system(module, client_factory)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
