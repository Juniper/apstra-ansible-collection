#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: allowed_list

short_description: Manage platform-level IP/subnet allow list in Apstra

version_added: "1.2.0"

author:
  - "Shirish Ranoji (@sranoji)"

description:
  - Manage platform-level IP/subnet allow list (white-list) in Apstra.
  - Trusted IP/subnets are never locked out, even if they violate rate limit rules.
  - Maps to C(/api/aaa/ratelimit/allowlist).
  - Supports IP/subnet add (create), edit (update), delete, and list operations.
  - Changes to the allowed list are recorded in the event log.

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
      - IP address or subnet CIDR notation to add/remove from the allow list.
      - Required for C(state) C(present) or C(absent).
      - Examples: C(192.168.1.10), C(10.0.0.0/24), C(2001:db8::1/32).
    type: str
    required: false

  comment:
    description:
      - Optional comment/description for the IP/subnet.
      - Applicable when C(state) is C(present).
    type: str
    required: false

  state:
    description:
      - Desired state of the allow list entry.
      - C(present) - add or update an IP/subnet (default).
      - C(absent) - remove an IP/subnet.
      - C(list) - retrieve all entries in the allow list.
    type: str
    required: false
    choices: ["present", "absent", "list"]
    default: "present"
"""

EXAMPLES = """
- name: Add IP address to allowed list with comment
  juniper.apstra.allowed_list:
    ip_subnet: "192.168.1.100"
    comment: "Management workstation"
    state: present

- name: Add subnet to allowed list
  juniper.apstra.allowed_list:
    ip_subnet: "10.0.0.0/8"
    comment: "Corporate network"
    state: present

- name: Update comment for existing allowed entry
  juniper.apstra.allowed_list:
    ip_subnet: "192.168.1.100"
    comment: "Updated management workstation"
    state: present

- name: Remove IP from allowed list
  juniper.apstra.allowed_list:
    ip_subnet: "192.168.1.100"
    state: absent

- name: List all allowed IPs/subnets
  juniper.apstra.allowed_list:
    state: list
  register: result

- name: Show all allowed entries
  debug:
    msg: "{{ result.allowed_list }}"
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

allowed_list:
  description: List of all IP/subnet entries in the allowed list.
  type: list
  returned: when state is C(list)
  sample:
    - ip_subnet: "192.168.1.100"
      comment: "Management workstation"
    - ip_subnet: "10.0.0.0/8"
      comment: "Corporate network"

entry:
  description: The created or updated allow list entry.
  type: dict
  returned: when state is C(present) and change is made
  sample:
    ip_subnet: "192.168.1.100"
    comment: "Management workstation"

id:
  description: The ID of the entry.
  type: str
  returned: when entry exists
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


def _list_allowed_entries(client):
    """Retrieve all entries from the allowed list."""
    try:
        response = client.ratelimit.allowlist.list()
        if isinstance(response, dict):
            return response.get("items", [])
        return response or []
    except Exception as exc:
        return None, f"Failed to list allowed entries: {exc}"


def _find_entry_by_ip(client, ip_subnet):
    """Find an allow list entry by IP/subnet."""
    entries = _list_allowed_entries(client)
    if entries is None:
        return None

    for entry in entries:
        if isinstance(entry, dict) and entry.get("subnet") == ip_subnet:
            return entry
    return None


def _create_entry(client, ip_subnet, comment=None):
    """Create a new allowed list entry."""
    try:
        data = {"subnet": ip_subnet}
        if comment:
            data["comment"] = comment

        result = client.ratelimit.allowlist.create(data=data)
        return result, None
    except Exception as exc:
        return None, str(exc)


def _update_entry(client, ip_subnet, comment=None):
    """Update an existing allowed list entry (PATCH operation)."""
    try:
        data = {"subnet": ip_subnet}
        if comment:
            data["comment"] = comment

        result = client.ratelimit.allowlist.update(data=data)
        return result, None
    except Exception as exc:
        return None, str(exc)


def _delete_entry(client, ip_subnet):
    """Delete an allowed list entry."""
    try:
        # The SDK's delete_single method expects a string (the subnet)
        result = client.ratelimit.allowlist.delete_single(ip_subnet)
        return result, None
    except Exception as exc:
        return None, str(exc)


def run_module():
    module_args = apstra_client_module_args()
    module_args.update(
        dict(
            ip_subnet=dict(type="str", required=False),
            comment=dict(type="str", required=False),
            state=dict(
                type="str",
                choices=["present", "absent", "list"],
                default="present",
            ),
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    state = module.params["state"]
    ip_subnet = module.params["ip_subnet"]
    comment = module.params["comment"]

    # Validate required parameters
    if state in ["present", "absent"] and not ip_subnet:
        module.fail_json(
            msg=f"ip_subnet is required when state is '{state}'"
        )

    try:
        client = _get_client(module)

        if state == "list":
            entries = _list_allowed_entries(client)
            if entries is None:
                module.fail_json(msg="Failed to retrieve allowed list entries")
            module.exit_json(changed=False, allowed_list=entries)

        elif state == "absent":
            # Check if entry exists
            existing = _find_entry_by_ip(client, ip_subnet)
            if not existing:
                module.exit_json(changed=False, message=f"Entry {ip_subnet} not found")

            # Delete the entry
            result, error = _delete_entry(client, ip_subnet)
            if error:
                module.fail_json(msg=f"Failed to delete entry: {error}")

            module.exit_json(
                changed=True,
                message=f"Allowed list entry {ip_subnet} deleted",
            )

        else:  # state == "present"
            # Check if entry exists
            existing = _find_entry_by_ip(client, ip_subnet)

            if existing:
                # Entry exists, check if update is needed
                existing_comment = existing.get("comment", "")
                new_comment = comment or ""

                if existing_comment == new_comment:
                    # No changes
                    module.exit_json(
                        changed=False,
                        message=f"Allowed list entry {ip_subnet} already exists",
                        entry=existing,
                    )
                else:
                    # Update the entry
                    result, error = _update_entry(client, ip_subnet, comment)
                    if error:
                        module.fail_json(msg=f"Failed to update entry: {error}")

                    module.exit_json(
                        changed=True,
                        message=f"Allowed list entry {ip_subnet} updated",
                        entry=result or {"subnet": ip_subnet, "comment": comment},
                    )
            else:
                # Create new entry
                result, error = _create_entry(client, ip_subnet, comment)
                if error:
                    module.fail_json(msg=f"Failed to create entry: {error}")

                module.exit_json(
                    changed=True,
                    message=f"Allowed list entry {ip_subnet} created",
                    entry=result or {"subnet": ip_subnet, "comment": comment},
                )

    except Exception as exc:
        module.fail_json(msg=f"Unexpected error: {exc}\n{traceback.format_exc()}")


def main():
    run_module()


if __name__ == "__main__":
    main()
