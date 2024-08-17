from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.connection.apstra_connection import Connection
import sys

def main():
    module_args = dict(
        available_network_resources=dict(type='bool', required=False, default=False),
        gather_network_resources=dict(type='list', elements='str', required=False, default=[]),
        gather_subset=dict(type='list', elements='str', required=False, default=[]),
    )

    result = dict(
        changed=False,
        ansible_facts={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        # Instantiate the Connection class
        apstra_connection = Connection(module._play_context)
        
        # Gather facts using the persistent connection
        facts = apstra_connection.gather_facts(
            available_network_resources=module.params['available_network_resources'],
            gather_network_resources=module.params['gather_network_resources'],
            gather_subset=module.params['gather_subset'] 
        )
        
        # Set the gathered facts in the result
        result['ansible_facts'] = facts

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()