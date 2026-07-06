#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: aaa_server

short_description: Manage AAA (RADIUS) servers in an Apstra blueprint

version_added: "1.1.0"

author:
  - "Prabhanjan K V (@prabhanjankv)"

description:
  - This module allows you to create, update, delete, and list AAA servers
    within an Apstra blueprint.
  - AAA servers are used for 802.1x port-based authentication (RADIUS) and
    RADIUS Change of Authorization (CoA) configuration applied across the fabric.
  - The Apstra blueprint AAA server API currently supports RADIUS server types
    only (C(radius_dot1x) and C(radius_coa)). TACACS is not yet supported by the
    Apstra API; AAA configuration that requires TACACS should continue to use
    configlet templates.
  - The Apstra SDK does not expose a blueprint AAA server client, so this module
    communicates with the C(/api/blueprints/{id}/aaa-servers) endpoint directly.
options:
  api_url:
    description:
      - The URL used to access the Apstra api.
    type: str
    required: false
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
  password:
    description:
      - The password for authentication.
    type: str
    required: false
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  id:
    description:
      - Dictionary containing the blueprint and AAA server IDs.
      - The C(blueprint) key may be a blueprint UUID or label.
      - The C(aaa_server) key is the AAA server ID and is only required when
        targeting an existing server directly (otherwise the server is located
        by its C(label)).
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the AAA server object details.
      - Required keys for create are C(label), C(hostname), C(key) and
        C(server_type).
      - C(label) - unique name for the AAA server.
      - C(hostname) - the server IP address or DNS name.
      - C(key) - the encryption key / shared secret used by the AAA server.
        This value is sensitive, is never returned by the Apstra API, and is
        masked in module output.
      - C(server_type) - one of C(radius_dot1x) (802.1x RADIUS servers) or
        C(radius_coa) (RADIUS Dynamic Authorization / Change of Authorization
        servers).
      - C(auth_port) - (optional) authentication port. Defaults are chosen by
        Apstra (1812 for C(radius_dot1x), 3799 for C(radius_coa)). For
        C(radius_coa) the port can only be 3799.
      - C(acct_port) - (optional) accounting port. For C(radius_dot1x) this
        defaults to 1813. Set to C(null) to disable accounting. Not applicable
        to C(radius_coa).
    required: false
    type: dict
  state:
    description:
      - Desired state of the AAA server.
      - Use C(list) to enumerate all AAA servers in the blueprint.
    required: false
    type: str
    choices: ["present", "absent", "list"]
    default: "present"
"""

EXAMPLES = """
- name: Create a RADIUS 802.1x AAA server
  juniper.apstra.aaa_server:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "radius-1"
      hostname: "10.1.1.10"
      key: "{{ vault_radius_secret }}"
      server_type: "radius_dot1x"
      auth_port: 1812
      acct_port: 1813
    state: present

- name: Create a RADIUS Change of Authorization server
  juniper.apstra.aaa_server:
    id:
      blueprint: "my-blueprint"
    body:
      label: "radius-coa-1"
      hostname: "10.1.1.20"
      key: "{{ vault_radius_secret }}"
      server_type: "radius_coa"
    state: present

- name: Update an AAA server's hostname (located by label)
  juniper.apstra.aaa_server:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "radius-1"
      hostname: "10.1.1.11"
    state: present

- name: Update an AAA server by ID
  juniper.apstra.aaa_server:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      aaa_server: "o3PSx0QW1qh7NyqZoQ"
    body:
      auth_port: 1645
    state: present

- name: List all AAA servers in a blueprint
  juniper.apstra.aaa_server:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    state: list

- name: Delete an AAA server by label
  juniper.apstra.aaa_server:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "radius-1"
    state: absent

- name: Delete an AAA server by ID
  juniper.apstra.aaa_server:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      aaa_server: "o3PSx0QW1qh7NyqZoQ"
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
changes:
  description: Dictionary of updates that were applied.
  type: dict
  returned: on update
response:
  description:
    - The AAA server object details. The C(key) (shared secret) is never
      included.
  type: dict
  returned: when state is present and changes are made
id:
  description: The blueprint and AAA server IDs.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "aaa_server": "o3PSx0QW1qh7NyqZoQ"
  }
aaa_server:
  description:
    - The AAA server object details. The C(key) (shared secret) is never
      included because the Apstra API does not return it.
  type: dict
  returned: on create or update
  sample: {
      "id": "o3PSx0QW1qh7NyqZoQ",
      "label": "radius-1",
      "hostname": "10.1.1.10",
      "server_type": "radius_dot1x",
      "auth_port": 1812,
      "acct_port": 1813
  }
aaa_servers:
  description: List of all AAA servers in the blueprint.
  returned: when state is list
  type: list
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

# Maximum tries / delay when reading back objects from the eventually
# consistent AAA server API after a write.
_READ_RETRY = 10
_READ_DELAY = 3

# Creating an AAA server immediately after a blueprint is created can return a
# transient 404 until the blueprint's staging graph is fully built. This window
# can exceed a minute, so allow a generous retry budget. The retry only triggers
# on the transient 404, so targeting an existing blueprint is unaffected.
_CREATE_RETRY = 60
_CREATE_DELAY = 3

# Sensitive field that must never be returned to the user.
_SECRET_KEY = "key"


def _is_transient_not_found(error):
    """Return True if an exception message indicates a transient 404."""
    message = str(error)
    return "404" in message or "Resource not found" in message


def _aaa_url(blueprint_id, server_id=None):
    """Build the AAA server API URL for a blueprint (and optional server).

    The base client already prepends the scheme/host portion whose path ends
    with ``/api``, so paths built here must *not* include a leading ``/api``
    segment -- only the resource path starting with ``/blueprints/...``.
    """
    base = f"/blueprints/{blueprint_id}/aaa-servers"
    if server_id:
        return f"{base}/{server_id}"
    return base


def _strip_secret(obj):
    """Return a copy of an AAA server dict without the sensitive key."""
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k != _SECRET_KEY}
    return obj


def _api_list(base_client, blueprint_id):
    """List all AAA servers in a blueprint, returning a list of dicts."""
    try:
        response = base_client._request(url=_aaa_url(blueprint_id), method="GET")
    except Exception as e:  # noqa: BLE001 - tolerate transient 404s
        # Right after blueprint creation this endpoint can briefly return 404.
        if _is_transient_not_found(e):
            return []
        raise
    if not response:
        return []
    items = response.get("items", {}) if isinstance(response, dict) else response
    if isinstance(items, dict):
        return list(items.values())
    if isinstance(items, list):
        return items
    return []


def _api_get(base_client, blueprint_id, server_id, retry=0, retry_delay=_READ_DELAY):
    """Get a single AAA server by ID, tolerating eventual consistency lag."""
    from time import sleep

    last_exc = None
    for attempt in range(retry + 1):
        try:
            response = base_client._request(
                url=_aaa_url(blueprint_id, server_id), method="GET"
            )
            if response and isinstance(response, dict) and "id" in response:
                return response
        except Exception as e:  # noqa: BLE001 - tolerate transient 404s
            last_exc = e
        if attempt < retry:
            sleep(retry_delay)
    if last_exc is not None:
        return None
    return None


def _find_by_label(base_client, blueprint_id, label, retry=0, retry_delay=_READ_DELAY):
    """Locate an AAA server ID by its label, tolerating consistency lag."""
    from time import sleep

    for attempt in range(retry + 1):
        for server in _api_list(base_client, blueprint_id):
            if isinstance(server, dict) and server.get("label") == label:
                return server.get("id")
        if attempt < retry:
            sleep(retry_delay)
    return None


def _api_create(base_client, blueprint_id, body, retry=0, retry_delay=_READ_DELAY):
    """Create an AAA server.

    Immediately after a blueprint is created its AAA server endpoint may
    transiently return a 404 ("Resource not found") until the staging graph is
    ready. Retry on that transient condition so callers can configure AAA
    servers right after creating a blueprint.
    """
    from time import sleep

    last_exc = None
    for attempt in range(retry + 1):
        try:
            return base_client._request(
                url=_aaa_url(blueprint_id), method="POST", data=body
            )
        except Exception as e:  # noqa: BLE001
            # Only retry the transient "blueprint not ready" 404.
            if not _is_transient_not_found(e):
                raise
            last_exc = e
            if attempt < retry:
                sleep(retry_delay)
    raise last_exc


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent", "list"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    leaf_object_type = "aaa_server"

    try:
        # Instantiate the client factory and get the base SDK client. The SDK
        # has no blueprint AAA server client, so all CRUD is done via the
        # blueprint aaa-servers REST endpoint directly.
        client_factory = ApstraClientFactory.from_params(module)
        base_client = client_factory.get_base_client()

        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]

        # Resolve blueprint name to ID if needed
        if "blueprint" not in id or not id["blueprint"]:
            raise ValueError("Must specify 'blueprint' in 'id'.")
        blueprint_id = client_factory.resolve_blueprint_id(id["blueprint"])
        id["blueprint"] = blueprint_id

        # Make sure the shared secret is never logged or echoed back.
        if body and body.get(_SECRET_KEY):
            module.no_log_values.add(body[_SECRET_KEY])

        # --- State: list ---
        if state == "list":
            servers = _api_list(base_client, blueprint_id)
            result["aaa_servers"] = [_strip_secret(s) for s in servers]
            result["changed"] = False
            result["msg"] = "AAA servers listed successfully"
            module.exit_json(**result)
            return

        server_id = id.get(leaf_object_type, None)

        # Locate the server by label if no explicit ID was supplied.
        lookup_label = body.get("label") if body else None
        if server_id is None and lookup_label:
            server_id = _find_by_label(base_client, blueprint_id, lookup_label)
            if server_id:
                id[leaf_object_type] = server_id

        # Fetch the current object if we have an ID.
        current_object = None
        if server_id:
            current_object = _api_get(base_client, blueprint_id, server_id)

        # --- State: absent ---
        if state == "absent":
            if current_object:
                base_client._request(
                    url=_aaa_url(blueprint_id, server_id), method="DELETE"
                )
                result["changed"] = True
                result["id"] = id
                result["msg"] = "aaa_server deleted successfully"
            else:
                result["changed"] = False
                result["msg"] = "aaa_server not found, nothing to delete"
            module.exit_json(**result)
            return

        # --- State: present ---
        if current_object:
            result["id"] = id
            if body:
                # Determine the changes. The secret 'key' is never returned by
                # the API, so compare_and_update will not flag it; this keeps
                # the module idempotent.
                changes = {}
                if client_factory.compare_and_update(current_object, body, changes):
                    base_client._request(
                        url=_aaa_url(blueprint_id, server_id),
                        method="PATCH",
                        data=changes,
                    )
                    result["changed"] = True
                    result["changes"] = _strip_secret(changes)
                    result["msg"] = "aaa_server updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = "No changes needed for aaa_server"
            else:
                result["changed"] = False
                result["msg"] = "No changes specified for aaa_server"
        else:
            if body is None:
                raise ValueError("Must specify 'body' to create a aaa_server")
            # Validate required fields up-front for a clear error message.
            missing = [
                f
                for f in ("label", "hostname", _SECRET_KEY, "server_type")
                if not body.get(f)
            ]
            if missing:
                raise ValueError(
                    "Missing required body fields to create aaa_server: "
                    + ", ".join(missing)
                )
            created = _api_create(
                base_client,
                blueprint_id,
                body,
                retry=_CREATE_RETRY,
                retry_delay=_CREATE_DELAY,
            )
            server_id = created["id"]
            id[leaf_object_type] = server_id
            result["id"] = id
            result["changed"] = True
            result["response"] = _strip_secret(created)
            result["msg"] = "aaa_server created successfully"

        # Return the final object state. The API is eventually consistent, so
        # retry the read until the object materialises and reflects any
        # changes we just applied.
        from time import sleep as _sleep

        expected_changes = result.get("changes", {})
        for _read_attempt in range(_READ_RETRY + 1):
            final_object = _api_get(base_client, blueprint_id, server_id)
            if final_object:
                # After an update, wait until the read-back reflects the
                # changes we sent so the returned object is consistent.
                if expected_changes and not all(
                    final_object.get(k) == v for k, v in expected_changes.items()
                ):
                    if _read_attempt < _READ_RETRY:
                        _sleep(_READ_DELAY)
                        continue
                result[leaf_object_type] = _strip_secret(final_object)
                break
            if _read_attempt < _READ_RETRY:
                _sleep(_READ_DELAY)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
