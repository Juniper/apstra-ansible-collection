DOCUMENTATION = '''
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
'''

EXAMPLES = '''
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
'''

RETURN = '''
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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import apstra_client_module_args, ApstraClientFactory

def get_resource_map(module, client, blueprints, resource_type):
    """
    Retrieve a dictionary of objects of the specified type for a given blueprint_id, indexed by their id.

    :param module: The Ansible module.
    :param client: The Apstra client instance.
    :param blueprints: The list of blueprints.
    :param resource_type: The type of resource to retrieve (e.g., 'config_templates').
    """
    for blueprint in blueprints:
        blueprint_id = blueprint['id']

        # Traverse nested resource_type
        resource = client.blueprints[blueprint_id]
        for attr in resource_type.split('.'):
            resource = getattr(resource, attr, None)
            if resource is None:
                module.fail_json(msg=f"Resource type '{resource_type}' not found for blueprint {blueprint_id}")

        resources = None
        if hasattr(resource, 'list'):
            try:
                resources = resource.list()
            except TypeError as te:
                # Bug -- 404 results in None, which generated API blindly subscripts
                if (te.args[0] == "'NoneType' object is not subscriptable"):
                    resources = {}
        else:
            # resource should have an id
           resources = resource.get() 
        
        # Ensure resources is a list or dict
        if isinstance(resources, list):
            resource_map = {item['id']: item for item in resources}
            blueprint[resource_type] = resource_map
        elif isinstance(resources, dict):
            blueprint[resource_type] = resources
        elif 'id' in resources:
            blueprint[resource_type] = {resources['id']: resource}
        else:
            module.fail_json(msg=f"Expected resources to be a list or dict or support get, got {type(resources)}")
        
def main():
    facts_module_args = dict(
        available_network_resources=dict(type='bool', required=False, default=False),
        gather_network_resources=dict(type='list', elements='str', required=False, default=['blueprints']),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | facts_module_args 

    result = dict(
        changed=False,
        ansible_facts={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        # Instantiate the client
        client_factory = ApstraClientFactory.from_params(module.params)
        base_client = client_factory.get_base_client()
        l3clos_client = client_factory.get_l3clos_client()
        freeform_client = client_factory.get_freeform_client()
        endpointpolicy_client = client_factory.get_endpointpolicy_client()
        tags_client = client_factory.get_tags_client()

        # Map client to types. Dotted types are traversed.
        client_to_types = {
            freeform_client: ['config_templates'],
            l3clos_client: ['virtual_networks', 'routing_zone_constraints'],
            endpointpolicy_client: ['endpoint_policies', 'obj_policy_application_points'],
            tags_client : ['tags'],
        }

        # Get the list of supported objects
        network_resources = []
        network_resources_set = {}
        for resource_client, resource_types in client_to_types.items():
            for resource_type in resource_types:
                network_resources.append(resource_type)
                # Map the resource type to the client
                network_resources_set[resource_type] = resource_client

        # If requested, add the available network resources to the result
        if module.params['available_network_resources']:
            result['available_network_resources'] = network_resources
        
        # Gather facts using the persistent connection

        # Get /api/version
        version = base_client.version.get()
        
        # Get /api/blueprints, as it's a root for many objects
        blueprints = base_client.blueprints.list()
        blueprints_map = {blueprint['id']: blueprint for blueprint in blueprints}

        # Process the list of requested network resources
        requested_network_resources = {}
        for resource_type in module.params['gather_network_resources']:
            if resource_type == 'all':
                requested_network_resources = network_resources_set
                break
            elif resource_type == 'blueprints':
                # Already gathered
                pass
            elif resource_type in network_resources_set:
                # Map the resource type to the client
                requested_network_resources[resource_type] = network_resources_set[resource_type]
            else:
                module.fail_json(msg=f"Unsupported network resource '{resource_type}'")

        # Get the resources
        for resource_type, resource_client in requested_network_resources.items():
            get_resource_map(module, resource_client, blueprints, resource_type)

        # Example of gathering facts
        facts = {
            'version': version,
            'blueprints': blueprints_map,
        }
        
        # Set the gathered facts in the result
        result['ansible_facts'] = facts

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()