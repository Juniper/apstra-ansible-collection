from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import apstra_client_module_args, apstra_client

def main():
    facts_module_args = dict(
        available_network_resources=dict(type='bool', required=False, default=False),
        gather_network_resources=dict(type='list', elements='str', required=False, default=[]),
        gather_subset=dict(type='list', elements='str', required=False, default=[]),
    )
    client_module_args = apstra_client_module_args()
    module_args = facts_module_args | client_module_args

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
        client = apstra_client(module.params)
        
        # Gather facts using the persistent connection

        # Get /api/version
        version = client.version.get()
        
        # Get /api/blueprints
        blueprints = client.blueprints.list()
        blueprints_map = {blueprint['id']: blueprint for blueprint in blueprints}
        
        # Get /api/blueprints/{blueprint_id}/routing-zone-constraints
        # for id, blueprint in blueprints_map.items():
        #     routing_zone_constraints = client.blueprints[id].routing_zone_constraints.list()
        #     for constraint in routing_zone_constraints:
        #         blueprint['routing_zone_constraints'][constraint[id]] = constraint
        
        # # Get /api/blueprints/{blueprint_id}/config-templates
        # for blueprint in blueprints:
        #     config_templates = client.blueprints[blueprint['id']].config_templates.get()
        
        # # Get /api/blueprints/{{blueprint_id}}/endpoint-policies
        # for blueprint in blueprints:
        #     endpoint_policies = client.blueprints[blueprint['id']].endpoint_policies.get()
        
        # # Get /api/blueprints/{{blueprint_id}}/obj-policy-application-points
        # for blueprint in blueprints:
        #     obj_policy_application_points = client.blueprints[blueprint['id']].obj_policy_application_points.get()
        
        # Example of gathering facts
        facts = {
            'version': version,
            'blueprints': blueprints_map,
            # 'routing_zone_constraints': routing_zone_constraints,
            # 'config_templates': config_templates,
            # 'endpoint_policies': endpoint_policies,
            # 'obj_policy_application_points': obj_policy_application_points,
            # Add more facts as needed
        }
        
        # Set the gathered facts in the result
        result['ansible_facts'] = facts

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()