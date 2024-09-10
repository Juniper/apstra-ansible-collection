DOCUMENTATION = """
---
module: apstra_facts
short_description: Gather facts from Apstra AOS
description:
  - This module gathers facts from Apstra AOS, including information about
    config templates, virtual networks, routing zone constraints, endpoint policies,
    and object policy application points.
version_added: "1.0.0"
author: "Edwin Jacques (@edwinpjacques)"
options:
  gather_network_resources:
    description:
      - List of network resources to gather facts about.
      - Use 'all' to gather facts about all supported network resources.
    type: list
    elements: str
    required: true
  available_network_resources:
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
    gather_network_resources:
      - all

# Gather facts about specific network resources
- name: Gather specific Apstra facts
  apstra_facts:
    gather_network_resources:
      - config_templates
      - virtual_networks

# Get the list of available network resources
- name: List available Apstra network resources
  apstra_facts:
    gather_network_resources:
      - all
    available_network_resources: true
"""

RETURN = """
available_network_resources:
  description: List of available network resources that can be gathered.
  returned: when available_network_resources is true
  type: list
  sample: ['config_templates', 'virtual_networks', 'routing_zone_constraints', 'endpoint_policies', 'obj_policy_application_points']
facts:
  description: Dictionary containing the gathered facts.
  returned: always
  type: dict
  sample: {
    "config_templates": {...},
    "virtual_networks": {...},
    "routing_zone_constraints": {...},
    "endpoint_policies": {...},
    "obj_policy_application_points": {...}
  }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


def main():
    facts_module_args = dict(
        available_network_resources=dict(type="bool", required=False, default=False),
        gather_network_resources=dict(
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
        if module.params["available_network_resources"]:
            result["available_network_resources"] = client_factory.network_resources

        # Gather facts using the persistent connection

        # Get /api/version
        version = base_client.version.get()

        # Get /api/blueprints, as it's a root for many objects
        blueprints = base_client.blueprints.list()
        blueprints_map = {blueprint["id"]: blueprint for blueprint in blueprints}

        # Process the list of requested network resources
        requested_network_resources = []
        for resource_type in module.params["gather_network_resources"]:
            if resource_type == "all":
                requested_network_resources = client_factory.network_resources
                break
            elif resource_type == "blueprints":
                # Already gathered
                pass
            elif resource_type in client_factory.network_resources_set:
                # Add resource type to set
                requested_network_resources.append(resource_type)
            else:
                module.fail_json(msg=f"Unsupported network resource '{resource_type}'")

        # Get the resources
        for resource_type in requested_network_resources:
            client = client_factory.get_client(resource_type)
            for blueprint in blueprints:
                blueprint_id = blueprint["id"]

                # Traverse nested resource_type
                resource = client.blueprints[blueprint_id]
                for attr in resource_type.split("."):
                    resource = getattr(resource, attr, None)
                    if resource is None:
                        module.fail_json(
                            msg=f"Resource type '{resource_type}' not found for blueprint {blueprint_id}"
                        )

                resources = None
                if resource == None:
                    # The resource does not exist for the blueprint
                    pass
                elif hasattr(resource, "list"):
                    try:
                        resources = resource.list()
                    except TypeError as te:
                        # Bug -- 404 results in None, which generated API blindly subscripts
                        if te.args[0] == "'NoneType' object is not subscriptable":
                            resources = None
                else:
                    # the resource does not support list, so get it
                    resources = resource.get()

                # Save the resource(s) in the blueprint map
                blueprint[resource_type] = resources

        # Structure used for gathered facts
        facts = {
            "version": version,
            "blueprints": blueprints_map,
        }

        # Set the gathered facts in the result
        result["ansible_facts"] = facts

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
