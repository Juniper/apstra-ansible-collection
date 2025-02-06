#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# MIT License

from __future__ import absolute_import, division, print_function
import traceback

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

DOCUMENTATION = """
---
module: apstra_authenticate
short_description: Apstra authentication
description:
  - This module authenticates with Apstra and retrieves an authentication token.  It can also handle logout operations.
version_added: "0.1.0"
author: "Edwin Jacques (@edwinpjacques)"
options:
  api_url:
    description:
      - The URL used to access the Apstra api.
    type: str
    required: false
    default: APSTRA_API_URL environment variable
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
    default: APSTRA_USERNAME environment variable
  password:
    description:
      - The password for authentication.
    type: str
    required: false
    default: APSTRA_PASSWORD environment variable
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
    default: APSTRA_AUTH_TOKEN environment variable
  logout:
    description:
      - If set to true, the module will log out the current session.
    type: bool
    default: false
"""

EXAMPLES = """
# Authenticate with Apstra AOS and retrieve an auth token.
# Token can be read via {{ auth.token }}.
- name: Authenticate with Apstra AOS
  apstra_authenticate:
    api_url: "https://10.87.2.40/api"
    username: "admin"
    password: "password"
  register: auth

# Use an existing auth token
- name: Use existing auth token
  apstra_authenticate:
    api_url: "https://10.87.2.40/api"
    auth_token: "{{ auth.token }}"

# Log out from Apstra AOS
- name: Log out from Apstra AOS
  apstra_authenticate:
    api_url: "https://10.87.2.40/api"
    auth_token: "{{ auth.token }}"
    logout: true
"""

RETURN = """
token:
  description: The authentication token retrieved from Apstra AOS.
  returned: when not logging out
  type: str
  sample: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
"""


def main():
    authenticate_module_args = dict(
        logout=dict(type="bool", required=False, default=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | authenticate_module_args

    result = dict(changed=False, response="")

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        # If auth_token is already set, and we're not logging out, return the auth_token.
        if bool(client_factory.auth_token) and not client_factory.logout:
            module.exit_json(changed=False, token=module.auth_token)

        client_factory.get_base_client()

        if client_factory.logout:
            module.exit_json(changed=True)

        # Return the auth token
        module.exit_json(changed=True, token=client_factory.auth_token)
    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
