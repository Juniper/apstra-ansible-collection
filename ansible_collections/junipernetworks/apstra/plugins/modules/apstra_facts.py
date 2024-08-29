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
        
        # Get /api/blueprints/{blueprint_id}/routing-zone-constraints
        
        # Get /api/blueprints/{blueprint_id}/config-templates
        
        # Get /api/blueprints/{{blueprint_id}}/endpoint-policies
        
        # Get /api/blueprints/{{blueprint_id}}/obj-policy-application-points
        
        # Example of gathering facts
        facts = {
            'version': version,
            # Add more facts as needed
        }
        
        # Set the gathered facts in the result
        result['ansible_facts'] = facts

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()