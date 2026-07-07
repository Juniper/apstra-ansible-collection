#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: banned_list

short_description: Manage platform-level IP/subnet ban list (denylist) in Apstra

version_added: "1.1.0"

author:
  - "Shirish Ranoji (@sranoji)"

description:
  - Manage platform-level IP/subnet ban list (denylist) in Apstra.
  - IP/subnets that violate rate limit rules are automatically added to the
    banned list and are locked out for the configured lockout period.
  - Admins can remove IP/subnets from the banned list to immediately allow
    logins from that IP/subnet.
  - Maps to C(/api/aaa/ratelimit/denylist).
  - Supports IP/subnet delete and query operations only (entries are auto-added
    by the rate limiter).
  - Changes to the banned list are recorded in the event log.

options:
  api_url:
    description: Apstra API URL. Defaults to C(APSTRA_API_URL) env var.
    type: str
    required: false

  verify_certificates:
    description: Verify TLS certificates.
    type: bool
    required: false
    default: true

  username:
    description: Apstra username for SDK login. Defaults to C(APSTRA_USERNAME) env var.
    type: str
    required: false

  password:
    description: Apstra password for SDK login. Defaults to C(APSTRA_PASSWORD) env var.
    type: str
    required: false

  auth_token:
    description: Pre-existing auth token. Defaults to C(APSTRA_AUTH_TOKEN) env var.
    type: str
    required: false

  ip_subnet:
    description:
      - IP address or subnet CIDR notation to remove from the ban list.
      - Required for C(state) C(absent).
      - Note - entries cannot be manually created; they are automatically added
        by the rate limiter when IP/subnets violate rate limit rules.
      - Examples: C(192.168.1.10), C(10.0.0.0/24), C(2001:db8::1/32).
    type: str
    required: false

  state:
    description:
      - Desired state for ban list management.
      - C(absent) - remove an IP/subnet from the ban list.
      - C(query) - retrieve all entries in the ban list (default).
      - Note - C(present) is not supported since entries are auto-added.
    type: str
    required: false
    choices: ["absent", "query"]
    default: "query"
"""

EXAMPLES = """
- name: List all banned IP addresses
  juniper.apstra.banned_list:
    state: query
  register: result

- name: Show all banned entries
  debug:
    msg: "{{ result.banned_list }}"

- name: Remove IP from ban list (allow it to login again)
  juniper.apstra.banned_list:
    ip_subnet: "192.168.1.100"
    state: absent

- name: Unban a subnet
  juniper.apstra.banned_list:
    ip_subnet: "10.0.0.0/24"
    state: absent
"""

RETURN = """
changed:
  description: Whether any change was made.
  type: bool
  returned: always

message:
  description: Result message.
  type: str
  returned: always

banned_list:
  description: List of all IP/subnet entries in the ban list (denylist).
  type: list
  returned: when state is C(query)
  sample:
    - ip_subnet: "192.168.1.100"
    - ip_subnet: "10.0.0.0/24"

id:
  description: The ID of the entry removed (if applicable).
  type: str
  returned: when entry is removed
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


def _get_client(module):
    """Get authenticated Apstra client."""
    try:
        factory = ApstraClientFactory.from_params(module)
        return factory.get_base_client()
    except Exception as exc:
        module.fail_json(msg=f"Failed to authenticate to Apstra: {exc}")


def _list_banned_entries(client):
    """Retrieve all entries from the ban list (denylist)."""
    try:
        response = client.ratelimit.denylist.list()
        if isinstance(response, dict):
            return response.get("items", [])
        return response or []
    except Exception as exc:
        return None, f"Failed to list banned entries: {exc}"


def _find_entry_by_ip(client, ip_subnet):
    """Find a ban list entry by IP/subnet."""
    entries = _list_banned_entries(client)
    if entries is None:
        return None

    for entry in entries:
        if isinstance(entry, dict) and entry.get("subnet") == ip_subnet:
            return entry
    return None


def _delete_entry(client, ip_subnet):
    """Delete/remove a ban list entry."""
    try:
        # The SDK's delete_single method expects a string (the subnet)
        result = client.ratelimit.denylist.delete_single(ip_subnet)
        return result, None
    except Exception as exc:
        return None, str(exc)


def run_module():
    module_args = apstra_client_module_args()
    module_args.update(
        dict(
            ip_subnet=dict(type="str", required=False),
            state=dict(
                type="str",
          choices=["absent", "query"],
          default="query",
            ),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    state = module.params["state"]
    ip_subnet = module.params["ip_subnet"]

    # Validate required parameters
    if state == "absent" and not ip_subnet:
        module.fail_json(msg="ip_subnet is required when state is 'absent'")

    try:
        client = _get_client(module)

        if state == "query":
            entries = _list_banned_entries(client)
            if entries is None:
                module.fail_json(msg="Failed to retrieve banned list entries")
            module.exit_json(changed=False, banned_list=entries)

        elif state == "absent":
            # Check if entry exists
            existing = _find_entry_by_ip(client, ip_subnet)
            if not existing:
                module.exit_json(
                    changed=False,
                    message=f"Entry {ip_subnet} not found in ban list",
                )

            # Delete the entry
            result, error = _delete_entry(client, ip_subnet)
            if error:
                module.fail_json(msg=f"Failed to remove entry from ban list: {error}")

            module.exit_json(
                changed=True,
                message=f"Ban list entry {ip_subnet} removed",
            )

    except Exception as exc:
        module.fail_json(msg=f"Unexpected error: {exc}\n{traceback.format_exc()}")


def main():
    run_module()


if __name__ == "__main__":
    main()
