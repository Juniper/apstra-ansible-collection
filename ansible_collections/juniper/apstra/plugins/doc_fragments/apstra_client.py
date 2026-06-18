#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

class ModuleDocFragment:
    DOCUMENTATION = r'''
options:
  api_url:
    description:
      - The URL used to access the Apstra API.
    type: str
    required: false

  verify_certificates:
    description:
      - If set to false, SSL certificates will not be verified.
    type: bool
    required: false
    default: true

  username:
    description:
      - The username for authentication.
    type: str
    required: false

  password:
    description:
      - The password for authentication.
    type: str
    required: false
    no_log: true

  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
    no_log: true
'''
