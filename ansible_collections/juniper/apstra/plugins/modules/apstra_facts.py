#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import traceback

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

DOCUMENTATION = """
---
module: apstra_facts
short_description: Gather facts from Apstra AOS
description:
  - This module gathers facts from Apstra AOS, including information about
    blueprints, virtual networks, security zones, endpoint policies,
    and application points.
version_added: "0.1.0"
author: "Edwin Jacques (@edwinpjacques)"
options:
  api_url:
    description:
      - The URL used to access the Apstra api.
    type: str
    required: false
    env:
      - name: APSTRA_API_URL
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
    env:
      - name: APSTRA_USERNAME
  password:
    description:
      - The password for authentication.
    type: str
    required: false
    env:
      - name: APSTRA_PASSWORD
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
    env:
      - name: APSTRA_AUTH_TOKEN
  gather_network_facts:
    description:
      - List of network objects to gather facts about.
      - Use 'all' to gather facts about all supported network objects.
    type: list
    elements: str
    required: true
    default: ['blueprints']
  id:
    description:
      - Dictionary containing identifiers to focus us.
    required: false
    type: dict
    default: {}
  filter:
    description:
      - Filter used to get the list of objects.
      - Key is a type, value is a filter string.
    type: dict
    required: false
    default: "{'blueprints.nodes': 'node_type=system'}"
  available_network_facts:
    description:
      - If set to true, the module will return a list of available network objects.
    type: bool
    default: false
requirements:
  - "python >= 3.10"
  - "apstra-client >= 1.0.0"
"""

EXAMPLES = """
# Gather facts about all network objects
- name: Gather all Apstra facts
  apstra_facts:
    gather_network_facts:
      - all

# Gather facts about specific network objects for a blueprint
- name: Gather specific Apstra facts
  apstra_facts:
    gather_network_facts:
      - virtual_networks
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"

# Gather facts about system nodes in the blueprint
- name: Gather system nodes
  apstra_facts:
    gather_network_facts:
      - blueprints.nodes
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    filter:
      blueprints.nodes: "node_type=system"

# Get the list of available network objects
- name: List available Apstra network objects
  apstra_facts:
    gather_network_facts:
      - all
    available_network_facts: true
"""

RETURN = """
available_network_facts:
  description: List of available network objects that can be gathered.
  returned: when available_network_facts is true
  type: list
  sample: ['blueprint.virtual_networks', 'blueprint.security_zones', 'blueprint.endpoint_policies', 'blueprint.endpoint_policies.application_points']
ansible_facts:
  description: Dictionary containing the gathered facts.
  returned: always
  type: dict
  sample: {
    "apstra_version": "5.0.0",
    "apstra_facts": {
      "blueprints": {
        "virtual_networks": {...},
        "routing_zone_constraints": {...},
        "endpoint_policies": {
          "application_points": {...}
        }
      }
    }
  }
"""


def main():
    facts_module_args = dict(
        id=dict(type="dict", required=False, default={}),
        available_network_facts=dict(type="bool", required=False, default=False),
        gather_network_facts=dict(
            type="list", elements="str", required=False, default=["blueprints"]
        ),
        filter=dict(
            type="dict",
            required=False,
            default={"blueprints.nodes": "node_type=system"},
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | facts_module_args

    result = dict(changed=False, ansible_facts={})

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)
        base_client = client_factory.get_base_client()

        # If requested, add the available network objects to the result
        if module.params["available_network_facts"]:
            result["available_network_facts"] = client_factory.network_objects

        # Gather facts using the persistent connection

        # Get /api/version
        version = base_client.version.get()

        # client_factory.network_objects is a list of supported network objects
        # The objects are nested, like 'blueprints', 'blueprints.config_templates', etc.
        # Need to get the list in topological sort order.

        # Process the list of requested network objects
        requested_network_objects = []
        for object_type in module.params["gather_network_facts"]:
            if object_type == "all":
                requested_network_objects = client_factory.network_objects
                break
            elif object_type in client_factory.network_objects_set:
                # Add object type to set
                requested_network_objects.append(object_type)
            else:
                module.fail_json(msg=f"Unsupported network object '{object_type}'")

        # Iterate through the list of requested network objects and get everything.
        object_map = client_factory.list_all_objects(
            requested_network_objects, module.params.get("id", {})
        )

        # Structure used for gathered facts
        facts = {
            "apstra_version": version,
            "apstra_facts": object_map,
        }

        # Set the gathered facts in the result
        result["ansible_facts"] = facts

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
