from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import apstra_client_module_args, ApstraClientFactory

def main():
    module_args = apstra_client_module_args()

    result = dict(
        changed=False,
        response=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        client_factory = ApstraClientFactory.from_params(module.params)

        # If auth_token is already set, and we're not logging out, return the auth_token.
        if bool(client_factory.auth_token) and not client_factory.logout:
            module.exit_json(changed=False, auth_token=module.auth_token)
            return
        
        client = client_factory.client()

        if client_factory.logout:
            module.exit_json(changed=True)

        # Return the auth token
        module.exit_json(changed=True, auth_token=client_factory.auth_token)
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()