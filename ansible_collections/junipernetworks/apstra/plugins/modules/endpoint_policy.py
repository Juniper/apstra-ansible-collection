#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

DOCUMENTATION = """
---
module: endpoint_policy
short_description: Manage endpoint policies in Apstra
version_added: "0.1.0"
author:
  - "Edwin Jacques (@edwinpjacques)"
description:
  - This module allows you to create, update, and delete endpoint policies and application points in Apstra.
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
      - Dictionary containing the blueprint and endpoint policy IDs.
      - If only the blueprint ID is provided, the module will attempt to find the endpoint policy by label.
      - If the label is not provided, but a virtual_network_label parameter is given, the label will be
        used to find the endpoint policy associated with the virtual network with the matching label.
    required: true
    type: dict
  virtual_network_label:
    description:
      - The label of the virtual network to find the endpoint policy for. Used if the endpoing policy id and endpoint label are not provided.
    required: false
    type: str
  body:
    description:
      - Dictionary containing the endpoint policy object details.
      - If the body contains an entry named "application_points", it expected to be a list of dicts, each containing a "if_name" string and a "used" boolean to be used to patch the application points.
    required: false
    type: dict
  tags:
    description:
      - List of tags to apply to the endpoint policy.
  state:
    description:
      - Desired state of the endpoint policy.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
- name: Create an endpoint policy (or update it if the label exists)
  junipernetworks.apstra.endpoint_policy:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      description: "Example routing policy"
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

- name: Update an endpoint policy
  junipernetworks.apstra.endpoint_policy:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      endpoint_policy: "AjAuUuVLylXCUgAqaQ"
    body:
      description: "test VN description UPDATE"

- name: Update an endpoint policy application point
  junipernetworks.apstra.endpoint_policy:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    virtual_network_label: "vn25"
    body:
      application_points:
        - if_name: "xe-0/0/37"
          used: true
    state: present

- name: Delete an endpoint policy
  junipernetworks.apstra.endpoint_policy:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      endpoint_policy: "AjAuUuVLylXCUgAqaQ"
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
  description: The endpoint policy object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID of the created endpoint policy.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "endpoint_policy": "AjAuUuVLylXCUgAqaQ"
  }
endpoint_policy:
  description: The endpoint policy object details.
  returned: on create or update
  type: dict
  sample: {
      "id": "AjAuUuVLylXCUgAqaQ",
      "description": "Example routing policy",
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
      "label": "example_policy",
      "policy_type": "user_defined"
    }
tag_response:
  description: The response from applying tags to the endpoint policy.
  type: list
  returned: when tags are applied
  sample: ["red", "blue"]
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    singular_leaf_object_type,
    plural_leaf_object_type,
)

from aos.sdk.graph import query


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        virtual_network_label=dict(type="str", required=False),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        tags=dict(type="list", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        object_type = "blueprints.endpoint_policies"
        leaf_object_type = singular_leaf_object_type(object_type)
        application_points_object_type = (
            "blueprints.endpoint_policies.application_points"
        )
        application_point_leaf_object_type = singular_leaf_object_type(
            application_points_object_type
        )
        application_points_leaf_object_type = plural_leaf_object_type(
            application_points_object_type
        )

        # Validate params
        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]
        tags = module.params.get("tags", None)
        virtual_network_label = module.params.get("virtual_network_label", None)

        # Validate the id
        missing_id = client_factory.validate_id(object_type, id)
        if len(missing_id) > 1 or (
            len(missing_id) == 1
            and state == "absent"
            and missing_id[0] != leaf_object_type
        ):
            raise ValueError(f"Invalid id: {id} for desired state of {state}.")
        object_id = id.get(leaf_object_type, None)

        # Make the requested changes
        if state == "present":
            current_object = None
            if object_id is None:
                if body is None and not virtual_network_label:
                    raise ValueError(
                        f"Must specify 'body' to create a {leaf_object_type}"
                    )

                # See if the object label exists
                current_object = None
                if body and "label" in body:
                    id_found = client_factory.get_id_by_label(
                        id["blueprint"], "ep_endpoint_policy", body["label"]
                    )
                    if id_found:
                        id[leaf_object_type] = id_found
                        current_object = client_factory.object_request(
                            object_type, "get", id
                        )
                elif virtual_network_label:
                    # Get the endpoint id by label
                    ep_policy_by_vn = (
                        query.node(type="virtual_network", label=virtual_network_label)
                        .in_(type="vn_to_attach")
                        .node(type="ep_endpoint_policy")
                        .in_(type="ep_first_subpolicy")
                        .node(type="ep_endpoint_policy", policy_type_name="pipeline")
                        .in_(type="ep_subpolicy")
                        .node(
                            type="ep_endpoint_policy",
                            policy_type_name="batch",
                            name=leaf_object_type,
                        )
                    )
                    ep_found = client_factory.query_blueprint(
                        id["blueprint"], ep_policy_by_vn
                    )

                    if not ep_found:
                        module.fail_json(
                            msg=f"ep_endpoint_policy for virtual_network {virtual_network_label} not found"
                        )

                    if len(ep_found) > 1:
                        module.fail_json(
                            msg=f"Multiple ep_endpoint_policy object matching virtual_network {virtual_network_label} found: {ep_found}"
                        )

                    if leaf_object_type not in ep_found[0]:
                        module.fail_json(
                            msg=f"Object missing key {leaf_object_type}: {result[0]}"
                        )

                    # Finally, save the endpoint policy id
                    id[leaf_object_type] = ep_found[0][leaf_object_type].id

                    current_object = client_factory.object_request(
                        object_type, "get", id
                    )
                if current_object:
                    result["id"] = id
                else:
                    # Create the object
                    created_object = client_factory.object_request(
                        object_type, "create", id, body
                    )
                    object_id = created_object["id"]
                    id[leaf_object_type] = object_id
                    result["id"] = id
                    result["changed"] = True
                    result["response"] = created_object
                    result["msg"] = f"{leaf_object_type} created successfully"
            else:
                current_object = client_factory.object_request(object_type, "get", id)

            if current_object:
                current_object[application_point_leaf_object_type] = (
                    client_factory.object_request(
                        application_points_object_type, "get", id
                    )
                )
                if body:
                    # Track changes
                    changes = {}

                    # Update the application points if needed
                    if application_points_leaf_object_type in body:
                        if not virtual_network_label:
                            module.fail_json(
                                f"Must specify 'virtual_network_label' to update {application_points_leaf_object_type}"
                            )
                        app_points = []
                        for body_ap in body[application_points_leaf_object_type]:
                            ap = {}
                            if_name = body_ap["if_name"]
                            used = False

                            # Custom query to determine if the interface is associated with the virtual_network.
                            if_to_vn = (
                                query.node(
                                    type="interface", if_name=if_name, name="interface"
                                )
                                .out(type="ep_member_of")
                                .node(type="ep_group")
                                .in_(type="ep_affected_by")
                                .node(type="ep_application_instance")
                                .out(type="ep_nested")
                                .node(type="ep_endpoint_policy")
                                .out(type="vn_to_attach")
                                .node(
                                    type="virtual_network",
                                    label=virtual_network_label,
                                    name="virtual_network",
                                )
                            )

                            if_to_vn_found = client_factory.query_blueprint(
                                id["blueprint"], if_to_vn
                            )

                            if if_to_vn_found:
                                if len(if_to_vn_found) > 1:
                                    module.fail_json(
                                        msg=f"Multiple interface {if_name} to virtual_network {virtual_network_label} relations found: {if_to_vn_found}"
                                    )
                                if not "interface" in if_to_vn_found[0]:
                                    module.fail_json(
                                        msg=f"Object missing key 'interface': {if_to_vn_found[0]}"
                                    )
                                if not "virtual_network" in if_to_vn_found[0]:
                                    module.fail_json(
                                        msg=f"Object missing key 'virtual_network': {if_to_vn_found[0]}"
                                    )
                                # Mark this application point as in use
                                used = True

                            # If we are already at the desired state, skip the update
                            if used == body_ap["used"]:
                                continue

                            if if_to_vn_found and if_to_vn_found[0]:
                                # If we already know the interface id, use it
                                ap["id"] = if_to_vn_found[0]["interface"].id
                            else:
                                # Need to look up the interface id by label
                                ap["id"] = client_factory.get_id_by_label(
                                    blueprint_id=id["blueprint"],
                                    obj_type="interface",
                                    label=body_ap["if_name"],
                                    label_key="if_name",
                                )
                            if not ap["id"]:
                                module.fail_json(
                                    msg=f"Interface with label {body_ap['if_name']} not found"
                                )
                            ap["policies"] = [
                                {
                                    "policy": id[leaf_object_type],
                                    "used": body_ap["used"],
                                }
                            ]
                            app_points.append(ap)

                        if app_points:
                            client_factory.get_endpointpolicy_client().blueprints[
                                id["blueprint"]
                            ].obj_policy_batch_apply.patch(
                                {"application_points": app_points}
                            )
                            # Any ap changes are added to the changes dict
                            changes[application_point_leaf_object_type] = app_points

                    # Update the object
                    updated_object = {}
                    ep_changes = {}
                    if client_factory.compare_and_update(
                        current_object, body, ep_changes
                    ):
                        updated_object = client_factory.object_request(
                            object_type, "patch", id, ep_changes
                        )
                        # Need the response object to be a dict
                        if not isinstance(dict, updated_object):
                            updated_object = {}
                        changes[leaf_object_type] = ep_changes

                    changed = True if app_points or ep_changes else False
                    result["changed"] = changed
                    if changed:
                        if updated_object:
                            result["response"] = updated_object
                        result["changes"] = changes
                        result["msg"] = f"{leaf_object_type} updated successfully"

            # Apply tags if specified
            if tags:
                result["tag_response"] = client_factory.update_tags(
                    id, leaf_object_type, tags
                )

            # Return the final object state
            result[leaf_object_type] = client_factory.object_request(
                object_type, "get", id
            )
            result[leaf_object_type][application_points_leaf_object_type] = (
                client_factory.object_request(application_points_object_type, "get", id)
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
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
