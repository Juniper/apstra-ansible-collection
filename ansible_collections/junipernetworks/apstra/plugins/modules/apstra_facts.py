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
  gather_network_facts:
    description:
      - List of network resources to gather facts about.
      - Use 'all' to gather facts about all supported network resources.
    type: list
    elements: str
    required: true
  id:
    description:
      - Dictionary containing identifiers to focus us.
    required: false
    type: dict
  available_network_facts:
    description:
      - If set to true, the module will return a list of available network resources.
    type: bool
    default: false
requirements:
  - "python >= 3.10"
  - "apstra-client >= 1.0.0"
"""

EXAMPLES = """
# Gather facts about all network resources
- name: Gather all Apstra facts
  apstra_facts:
    gather_network_facts:
      - all

# Gather facts about specific network resources for a blueprint
- name: Gather specific Apstra facts
  apstra_facts:
    gather_network_facts:
      - virtual_networks
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"

# Get the list of available network resources
- name: List available Apstra network resources
  apstra_facts:
    gather_network_facts:
      - all
    available_network_facts: true
"""

RETURN = """
available_network_facts:
  description: List of available network resources that can be gathered.
  returned: when available_network_facts is true
  type: list
  sample: ['blueprint.virtual_networks', 'blueprint.security_zones', 'blueprint.endpoint_policies', 'blueprint.endpoint_policies.application_points']
facts:
  description: Dictionary containing the gathered facts.
  returned: always
  type: dict
  sample: {
    "blueprints": {
      "virtual_networks": {...},
      "routing_zone_constraints": {...},
      "endpoint_policies": {
        "application_points": {...}
      }
    }
  }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


def main():
    facts_module_args = dict(
        id=dict(type="dict", required=False, default={}),
        available_network_facts=dict(type="bool", required=False, default=False),
        gather_network_facts=dict(
            type="list", elements="str", required=False, default=["blueprints"]
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | facts_module_args

    result = dict(changed=False, ansible_facts={})

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module.params)
        base_client = client_factory.get_base_client()

        # If requested, add the available network resources to the result
        if module.params["available_network_facts"]:
            result["available_network_facts"] = client_factory.network_resources

        # Gather facts using the persistent connection

        # Get /api/version
        version = base_client.version.get()

        # client_factory.network_resources is a list of supported network resources
        # The resources are nested, like 'blueprints', 'blueprints.config_templates', etc.
        # Need to get the list in topological sort order.

        # Process the list of requested network resources
        requested_network_resources = []
        for resource_type in module.params["gather_network_facts"]:
            if resource_type == "all":
                requested_network_resources = client_factory.network_resources
                break
            elif resource_type in client_factory.network_resources_set:
                # Add resource type to set
                requested_network_resources.append(resource_type)
            else:
                module.fail_json(msg=f"Unsupported network resource '{resource_type}'")

        # Iterate through the list of requested network resources and get everything.
        resource_map = client_factory.list_all_resources(requested_network_resources, module.params.get("id", {}))

        # Structure used for gathered facts
        facts = {
            "version": version,
            "resources": resource_map,
        }

        # Set the gathered facts in the result
        result["ansible_facts"] = facts

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
