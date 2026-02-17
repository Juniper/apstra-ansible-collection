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
module: external_gateway

short_description: Manage external (remote) EVPN gateways in Apstra blueprints

version_added: "0.1.0"

author:
  - "Juniper Networks"

description:
  - This module allows you to create, update, and delete external
    (remote) EVPN gateways within an Apstra blueprint.
  - Remote EVPN Gateways are logical functions that can be instantiated
    on any device with BGP and L2VPN/EVPN AFI/SAFI support.
  - To establish a BGP session with an EVPN gateway, IP connectivity
    and access to TCP port 179 must be available.
  - This module operates at the blueprint scope and requires a
    Datacenter (two_stage_l3clos) design.

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
      - Dictionary containing the blueprint and remote gateway IDs.
      - C(blueprint) is always required.
      - C(remote_gateway) is optional for create (looked up by C(gw_name)
        from C(body) for idempotency), required for update/delete.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the external gateway details.
      - C(gw_name) (string) - Gateway name (required for create).
      - C(gw_ip) (string) - Gateway IPv4 or IPv6 address (required for
        create).
      - C(gw_asn) (integer) - Gateway AS number, 1-4294967295 (required
        for create).
      - C(local_gw_nodes) (list of strings) - IDs of AOS system nodes
        (spines, leafs, or superspines) that establish BGP EVPN peering
        with the remote gateway (required for create).
      - C(password) (string) - BGP session password (optional).
      - C(ttl) (integer) - Time to live in hops (optional).
      - C(keepalive_timer) (integer) - BGP keepalive timer in seconds
        (optional).
      - C(holdtime_timer) (integer) - BGP hold time timer in seconds
        (optional).
      - C(evpn_route_types) (string) - Permitted EVPN route types,
        C(all) or C(type5_only) (optional).
      - C(evpn_interconnect_group_id) (string) - Node ID of an EVPN
        interconnect group (optional).
    required: false
    type: dict
  state:
    description:
      - Desired state of the external gateway.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# Create an external gateway
- name: Create external gateway
  juniper.apstra.external_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      gw_name: "dc2_border_gw"
      gw_ip: "10.1.0.1"
      gw_asn: 65500
      local_gw_nodes:
        - "PPbnMs25oIuO8WHldA"
      ttl: 2
      keepalive_timer: 10
      holdtime_timer: 30
      evpn_route_types: "all"
    state: present
  register: ext_gw

# Update an external gateway
- name: Update external gateway
  juniper.apstra.external_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      remote_gateway: "{{ ext_gw.id.remote_gateway }}"
    body:
      gw_name: "dc2_border_gw"
      gw_ip: "10.1.0.2"
      gw_asn: 65501
      local_gw_nodes:
        - "PPbnMs25oIuO8WHldA"
      ttl: 5
    state: present

# Update by gw_name lookup (idempotent)
- name: Update external gateway by name
  juniper.apstra.external_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      gw_name: "dc2_border_gw"
      gw_ip: "10.1.0.3"
      gw_asn: 65502
      local_gw_nodes:
        - "PPbnMs25oIuO8WHldA"
    state: present

# Delete an external gateway
- name: Delete external gateway
  juniper.apstra.external_gateway:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      remote_gateway: "{{ ext_gw.id.remote_gateway }}"
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
  description: The external gateway object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID dictionary of the external gateway.
  returned: on create, or when object identified by gw_name
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "remote_gateway": "baV2vCzUKgv2mbYopw"
  }
remote_gateway:
  description: The external gateway object details.
  type: dict
  returned: on create or update
  sample: {
      "id": "baV2vCzUKgv2mbYopw",
      "gw_name": "dc2_border_gw",
      "gw_ip": "10.1.0.1",
      "gw_asn": 65500,
      "ttl": 2,
      "keepalive_timer": 10,
      "holdtime_timer": 30,
      "evpn_route_types": "all",
      "local_gw_nodes": [
          {
              "label": "spine1",
              "node_id": "PPbnMs25oIuO8WHldA",
              "role": "spine"
          }
      ]
  }
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


def _find_gateway_by_name(client_factory, object_type, id, gw_name):
    """
    Search for an existing remote gateway by gw_name in the list.

    :param client_factory: The ApstraClientFactory instance.
    :param object_type: The object type string.
    :param id: The id dictionary (must contain 'blueprint').
    :param gw_name: The gateway name to search for.
    :return: The matching gateway dict, or None.
    """
    all_gateways = client_factory.object_request(object_type, "get", id)
    if isinstance(all_gateways, list):
        for gw in all_gateways:
            if gw.get("gw_name") == gw_name:
                return gw
    elif isinstance(all_gateways, dict):
        # API returns {"remote_gateways": [...]}; SDK may unwrap it
        items = all_gateways.get("remote_gateways", all_gateways.values())
        for gw in items:
            if isinstance(gw, dict) and gw.get("gw_name") == gw_name:
                return gw
    return None


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
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

        object_type = "blueprints.remote_gateways"
        leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]

        # Coerce integer fields — Ansible may pass them as strings
        # when values come from Jinja2 templating
        _INT_FIELDS = ("gw_asn", "ttl", "keepalive_timer", "holdtime_timer")
        if body:
            for field in _INT_FIELDS:
                if field in body and body[field] is not None:
                    try:
                        body[field] = int(body[field])
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"'{field}' must be an integer, got: {body[field]!r}"
                        )

        # Validate the id
        missing_id = client_factory.validate_id(object_type, id)
        if len(missing_id) > 1 or (
            len(missing_id) == 1
            and state == "absent"
            and missing_id[0] != leaf_object_type
        ):
            raise ValueError(f"Invalid id: {id} for desired state of {state}.")
        object_id = id.get(leaf_object_type, None)

        # See if the object exists
        current_object = None
        if object_id is None:
            # Remote gateways use gw_name instead of label for lookup
            if (body is not None) and ("gw_name" in body):
                found = _find_gateway_by_name(
                    client_factory, object_type, id, body["gw_name"]
                )
                if found:
                    id[leaf_object_type] = found["id"]
                    current_object = found
        else:
            current_object = client_factory.object_request(object_type, "get", id)
            # SDK may return a list when calling list() on a specific item;
            # unwrap if needed
            if isinstance(current_object, list) and len(current_object) > 0:
                current_object = current_object[0]

        # Make the requested changes
        if state == "present":
            if current_object:
                result["id"] = id
                if body:
                    # Compare and update
                    # For remote_gateways, local_gw_nodes in GET response
                    # is expanded (list of dicts with node_id, label, role).
                    # We need to normalize for comparison.
                    compare_object = dict(current_object)
                    if "local_gw_nodes" in compare_object and isinstance(
                        compare_object["local_gw_nodes"], list
                    ):
                        # Normalize: extract node_id from expanded format
                        normalized = []
                        for node in compare_object["local_gw_nodes"]:
                            if isinstance(node, dict) and "node_id" in node:
                                normalized.append(node["node_id"])
                            else:
                                normalized.append(node)
                        compare_object["local_gw_nodes"] = sorted(normalized)

                    compare_body = dict(body)
                    if "local_gw_nodes" in compare_body and isinstance(
                        compare_body["local_gw_nodes"], list
                    ):
                        compare_body["local_gw_nodes"] = sorted(
                            compare_body["local_gw_nodes"]
                        )

                    changes = {}
                    if client_factory.compare_and_update(
                        compare_object, compare_body, changes
                    ):
                        # remote_gateways API uses PUT (full replace);
                        # send the complete desired body via 'update' op
                        updated_object = client_factory.object_request(
                            object_type, "update", id, body
                        )
                        result["changed"] = True
                        if updated_object:
                            result["response"] = updated_object
                        result["changes"] = changes
                        result["msg"] = f"{leaf_object_type} updated successfully"
                    else:
                        result["changed"] = False
                        result["msg"] = (
                            f"{leaf_object_type} already exists, no changes " f"needed"
                        )
                else:
                    result["changed"] = False
                    result["msg"] = f"No changes specified for {leaf_object_type}"
            else:
                if body is None:
                    raise ValueError(
                        f"Must specify 'body' to create a {leaf_object_type}"
                    )
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
                final_obj = client_factory.object_request(
                    object_type=object_type,
                    op="get",
                    id=id,
                    retry=10,
                    retry_delay=3,
                )
                # SDK may return a list; unwrap if needed
                if isinstance(final_obj, list) and len(final_obj) > 0:
                    final_obj = final_obj[0]
                result[leaf_object_type] = final_obj

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(f"Cannot manage a {leaf_object_type} without an object id")

        if state == "absent":
            if leaf_object_type not in id:
                raise ValueError(f"Must specify '{leaf_object_type}' in id to delete")
            client_factory.object_request(object_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{leaf_object_type} deleted successfully"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
