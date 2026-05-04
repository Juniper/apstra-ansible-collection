#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: security_zone

short_description: Manage security zones in Apstra

version_added: "0.1.0"

author:
  - "Edwin Jacques (@edwinpjacques)"

description:
  - This module allows you to create, update, and delete security zones in Apstra.

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
      - Dictionary containing the blueprint and security zone IDs.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the security zone object details.
    required: false
    type: dict
  tags:
    description:
      - List of tags to apply to the security zone.
    type: list
    elements: str
  state:
    description:
      - Desired state of the security zone.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Create a security zone
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      description: "Example security zone"
      expect_default_ipv4_route: true
      expect_default_ipv6_route: true
      export_policy:
        l2edge_subnets: true
        loopbacks: true
        spine_leaf_links: false
        spine_superspine_links: false
        static_routes: false
      import_policy: "all"
      label: "example_policy"
      policy_type: "user_defined"
    state: present

- name: Update a security zone (or update it if the label exists)
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      security_zone: "AjAuUuVLylXCUgAqaQ"
    body:
      description: "example security zone UPDATE"
      import_policy: "extra_only"
    state: present

- name: Delete a security zone
  juniper.apstra.security_zone:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      security_zone: "AjAuUuVLylXCUgAqaQ"
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
  description: The security zone object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the created security zone.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "security_zone": "AjAuUuVLylXCUgAqaQ"
  }
security_zone:
  description: The security zone object details.
  returned: on create or update
  type: dict
  sample: {
      "id": "AjAuUuVLylXCUgAqaQ",
      "label": "example_policy",
      "description": "example security zone",
      "expect_default_ipv4_route": true,
      "expect_default_ipv6_route": true,
      "export_policy": {
          "l2edge_subnets": true,
          "loopbacks": true,
          "spine_leaf_links": false,
          "spine_superspine_links": false,
          "static_routes": false
      },
      "import_policy": "all",
      "policy_type": "user_defined"
  }
tag_response:
  description: The response from applying tags to the security zone.
  type: list
  returned: when tags are applied
  sample: ["red", "blue"]
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
    singular_leaf_object_type,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_security_zone_id,
    resolve_vrf_interface_pair,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_nodes import (
    get_node,
    patch_node,
    node_needs_update,
)


def _apply_interface_ip_assignments(
    client_factory, blueprint_id, sz_id, assignments, result
):
    """Patch IP addresses on VRF interface endpoints.

    For each entry in *assignments*, resolves the interface within the
    security zone, then patches endpoint1 and (optionally) endpoint2
    with the specified IPv4 address / type.

    :param assignments: List of dicts, each with ``interface``,
        ``endpoint1_ipv4_address``, etc.
    :param result: Module result dict — ``changed`` and
        ``ip_assignments`` are updated in-place.
    """
    ip_results = []
    for assignment in assignments:
        interface_name = assignment["interface"]
        ep1_id, ep2_id = resolve_vrf_interface_pair(
            client_factory, blueprint_id, sz_id, interface_name
        )

        entry = {"interface": interface_name, "endpoint1_id": ep1_id}

        # ── Patch endpoint1 ──────────────────────────────────────
        if "endpoint1_ipv4_address" in assignment:
            ep1_props = {"ipv4_addr": assignment["endpoint1_ipv4_address"]}
            if "endpoint1_ipv4_type" in assignment:
                ep1_props["ipv4_type"] = assignment["endpoint1_ipv4_type"]
            current = get_node(client_factory, blueprint_id, ep1_id)
            changes = node_needs_update(current, ep1_props)
            if changes:
                patch_node(client_factory, blueprint_id, ep1_id, changes)
                result["changed"] = True
                entry["endpoint1_changed"] = True

        # ── Patch endpoint2 ──────────────────────────────────────
        if ep2_id and "endpoint2_ipv4_address" in assignment:
            ep2_props = {"ipv4_addr": assignment["endpoint2_ipv4_address"]}
            if "endpoint2_ipv4_type" in assignment:
                ep2_props["ipv4_type"] = assignment["endpoint2_ipv4_type"]
            current = get_node(client_factory, blueprint_id, ep2_id)
            changes = node_needs_update(current, ep2_props)
            if changes:
                patch_node(client_factory, blueprint_id, ep2_id, changes)
                result["changed"] = True
                entry["endpoint2_changed"] = True
            entry["endpoint2_id"] = ep2_id
        elif "endpoint2_ipv4_address" in assignment and not ep2_id:
            entry["endpoint2_warning"] = "No link partner found"

        ip_results.append(entry)

    result["ip_assignments"] = ip_results


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        tags=dict(type="list", elements="str", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        object_type = "blueprints.security_zones"
        leaf_object_type = singular_leaf_object_type(object_type)

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]
        tags = module.params.get("tags", None)

        # Pop custom fields that the Apstra API does not understand
        interfaces_ip_assignments = None
        sz_name = None
        if body:
            interfaces_ip_assignments = body.pop("interfaces_ip_assignments", None)
            sz_name = body.pop("sz_name", None)
            # Pop tags from body and merge with top-level tags parameter
            # Tags must go through update_tags(), not the create/patch API
            body_tags = body.pop("tags", None)
            if body_tags is not None:
                if tags is not None:
                    # Merge: top-level tags take precedence, add any from body
                    tags = list(set(tags) | set(body_tags))
                else:
                    tags = body_tags
            if sz_name:
                body.setdefault("label", sz_name)
                # When sz_name is the only source of "label" and no other
                # creation/update fields were supplied, mark this as a
                # lookup-only operation so we don't accidentally try to
                # create a VRF with incomplete data.
                if set(body.keys()) == {"label"}:
                    body = None
            elif not body:
                body = None

        # Resolve blueprint name to ID if needed
        if "blueprint" in id:
            id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])

        # Resolve security_zone name/label to ID if needed
        if leaf_object_type in id and id[leaf_object_type]:
            id[leaf_object_type] = resolve_security_zone_id(
                client_factory,
                id["blueprint"],
                id[leaf_object_type],
                raise_on_missing=True,
            )

        # Coerce integer fields that the API requires as int, not str
        if body:
            for int_field in ("vni_id", "vlan_id"):
                if int_field in body and body[int_field] is not None:
                    body[int_field] = int(body[int_field])

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
        lookup_label = (body or {}).get("label") or sz_name
        if object_id is None:
            if lookup_label:
                # All name resolution goes through resolve_security_zone_id
                # which checks: exact ID → label → case-insensitive label
                # → vrf_name → case-insensitive vrf_name.
                # When body is None (lookup-only via sz_name), raise if
                # not found; otherwise return None so creation can proceed.
                id_found = resolve_security_zone_id(
                    client_factory,
                    id["blueprint"],
                    lookup_label,
                    raise_on_missing=(body is None),
                )
            else:
                id_found = None

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
                    result["msg"] = f"No changes specified for {leaf_object_type}"
            else:
                if body is None:
                    raise ValueError(
                        f"Must specify 'body' to create a {leaf_object_type}"
                    )
                # Create the object
                object = client_factory.object_request(object_type, "create", id, body)
                object_id = object["id"]
                id[leaf_object_type] = object_id
                result["id"] = id
                result["changed"] = True
                result["response"] = object
                result["msg"] = f"{leaf_object_type} created successfully"

            # Apply tags if specified (tags=[] removes all tags)
            if tags is not None:
                result["tag_response"] = client_factory.update_tags(
                    id, leaf_object_type, tags
                )

            # Return the final object state (avoid re-reading after updates
            # because SDK may return stale cached data; for creates, fetch
            # the full server-populated object)
            if current_object is not None:
                result[leaf_object_type] = current_object
            else:
                result[leaf_object_type] = client_factory.object_request(
                    object_type=object_type, op="get", id=id, retry=10, retry_delay=3
                )

            # Apply interface IP assignments if specified
            if interfaces_ip_assignments:
                _apply_interface_ip_assignments(
                    client_factory,
                    id["blueprint"],
                    id[leaf_object_type],
                    interfaces_ip_assignments,
                    result,
                )

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError(f"Cannot manage a {leaf_object_type} without a object id")

        if state == "absent":
            # Delete the blueprint
            client_factory.object_request(object_type, "delete", id)
            result["changed"] = True
            result["msg"] = f"{leaf_object_type} deleted successfully"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
