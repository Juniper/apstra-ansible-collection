from ansible.module_utils.basic import AnsibleModule
from aos.sdk.client import Client
import os
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import apstra_client_module_args, apstra_client_auth_info
import sys

def main():
    authenticate_args = dict(
        username=dict(type='str', required=False),
        password=dict(type='str', required=False, no_log=True),
        logout=dict(type='bool', required=False, default=True)
    )
    client_module_args = apstra_client_module_args()
    module_args = authenticate_args | client_module_args

    result = dict(
        changed=False,
        response=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        api_url, verify_certificates, auth_token = apstra_client_auth_info(module.params)
        username = module.params['username'] or os.getenv('APSTRA_USERNAME')
        password = module.params['password'] or os.getenv('APSTRA_PASSWORD')
        logout = module.params['logout']

        if not api_url or (not auth_token and (not username or not password)):
            module.fail_json(msg="Missing required parameters: api_url, auth_token or (username and password)")

        # If auth_token is already set, and we're not logging out, return the auth_token.
        if hasattr(module, 'auth_token') and hasattr(module, 'username') and not logout:
            module.exit_json(changed=False, auth_token=module.auth_token, username=module.username)
            return

        client = Client(api_url, verify_certificates)

        # If not given an auth_token, create one.
        if auth_token:
            client.set_auth_token(auth_token)
        else:
            auth_token, username = client.login(username, password)

        if logout:
            # Add client to the play context (will clean up later)
            setattr(module, 'client', client)
            module.exit_json(changed=True)

        # Saved to avoid logging in needlessly in the same playbook
        setattr(module, 'auth_token', auth_token)
        setattr(module, 'username', username)

        # Return the auth token
        module.exit_json(changed=True, auth_token=auth_token, username=username)
    except Exception as e:
        module.fail_json(msg=str(e), **result)
    finally:
        client = getattr(module, 'client')
        if client:
            client.logout()

    module.exit_json(**result)

if __name__ == '__main__':
    main()