DOCUMENTATION = '''
---
module: apstra_authenticate
short_description: Authenticate with Apstra AOS and retrieve an auth token
description:
  - This module authenticates with Apstra AOS and retrieves an authentication token.
  - It can also handle logout operations.
version_added: "1.0.0"
author: "Edwin Jacques (@edwinpjacques)"
options:
  aos_ip:
    description:
      - The IP address of the Apstra AOS server.
    type: str
    required: true
  aos_port:
    description:
      - The port number of the Apstra AOS server.
    type: int
    required: true
  username:
    description:
      - The username for authentication.
    type: str
    required: true
  password:
    description:
      - The password for authentication.
    type: str
    required: true
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  logout:
    description:
      - If set to true, the module will log out the current session.
    type: bool
    default: false
requirements:
  - "python >= 3.10"
  - "apstra-client >= 1.0.0"
'''

EXAMPLES = '''
# Authenticate with Apstra AOS and retrieve an auth token
- name: Authenticate with Apstra AOS
  apstra_authenticate:
    aos_ip: "192.168.1.1"
    aos_port: 443
    username: "admin"
    password: "password"

# Use an existing auth token
- name: Use existing auth token
  apstra_authenticate:
    aos_ip: "192.168.1.1"
    aos_port: 443
    auth_token: "existing_token"

# Log out from Apstra AOS
- name: Log out from Apstra AOS
  apstra_authenticate:
    aos_ip: "192.168.1.1"
    aos_port: 443
    auth_token: "existing_token"
    logout: true
'''

RETURN = '''
token:
  description: The authentication token retrieved from Apstra AOS.
  returned: when not logging out
  type: str
  sample: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
'''

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
            module.exit_json(changed=False, token=module.auth_token)
        
        client_factory.get_base_client()

        if client_factory.logout:
            module.exit_json(changed=True)

        # Return the auth token
        module.exit_json(changed=True, token=client_factory.auth_token)
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()