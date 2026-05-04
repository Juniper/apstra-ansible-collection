#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: ztp_device

short_description: Manage ZTP (Zero Touch Provisioning) devices in Apstra

version_added: "0.1.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module allows you to create, delete, and check the status of
    ZTP (Zero Touch Provisioning) devices in Apstra.
  - ZTP devices are managed via the C(/api/ztp/device) API endpoint.
  - Device status can be retrieved using the
    C(/api/ztp/device/{ip_addr}/status) API endpoint by setting
    C(state) to C(status).
  - The ZTP device API does not support individual GET or PUT/PATCH
    operations. Updates are performed by deleting and recreating the
    device.
  - The module uses the Apstra SDK when available, falling back to
    direct API calls if necessary.

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
      - Dictionary containing the ZTP device identifier.
      - C(ip_addr) is the management IP address of the device.
      - C(system_id) is the system identifier of the device.
      - For C(status), either C(ip_addr) or C(system_id) must be provided.
      - For C(absent), C(ip_addr) is required.
      - For create, C(ip_addr) can be provided in the C(body) instead.
    required: false
    type: dict
  body:
    description:
      - Dictionary containing the ZTP device details.
      - Used for create and update operations.
      - C(ip_addr) (string) - Management IP address of the device (required for create).
      - C(system_id) (string) - System identifier for the device (required for create).
    required: false
    type: dict
  state:
    description:
      - Desired state of the ZTP device.
      - C(present) will create the device (or update via delete+recreate).
      - C(absent) will delete the device.
      - C(status) will retrieve the ZTP status of the device
        (requires C(ip_addr) or C(system_id) in C(id)).
    required: false
    type: str
    choices: ["present", "absent", "status"]
    default: "present"
"""

EXAMPLES = """
# Check ZTP device status by IP address
# Fails with an error if the IP address is not registered
- name: Get ZTP device status by IP
  juniper.apstra.ztp_device:
    id:
      ip_addr: "192.168.50.10"
    state: status
  register: ztp_status

- name: Show provisioning status (e.g. completed / unknown / in_progress)
  ansible.builtin.debug:
    msg: "ZTP status is {{ ztp_status.status }}"

# Check ZTP device status by system_id
# Fails with an error if no device with that system_id is registered
- name: Get ZTP device status by system_id
  juniper.apstra.ztp_device:
    id:
      system_id: "device-001"
    state: status
  register: ztp_status

- name: Show full ZTP device details
  ansible.builtin.debug:
    var: ztp_status.ztp_device
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
changes:
  description: Dictionary of fields that were updated (present only on update).
  type: dict
  returned: when state is present and an update was applied
response:
  description: Raw response from the API on create or update.
  type: dict
  returned: when state is present and changes are made
id:
  description: The identifier of the ZTP device (ip_addr).
  type: dict
  returned: always when a device is targeted
  sample: {
      "ip_addr": "192.168.50.10"
  }
ztp_device:
  description: Full ZTP device details retrieved from the status endpoint.
  type: dict
  returned: on create, update, or status check
  sample: {
      "ip_addr": "192.168.50.10",
      "system_id": "device-001",
      "task": "Device Ready",
      "status": "completed",
      "last_log": "Device is ready to be used",
      "last_updated_at": "2026-01-01T00:00:00.000000Z"
  }
ztp_devices:
  description: List of all registered ZTP devices.
  type: list
  returned: when state is present with no id and no body
  sample: [
      {
          "ip_addr": "192.168.50.10",
          "system_id": "device-001",
          "task": "Device Ready",
          "status": "completed",
          "last_log": "Device is ready to be used",
          "last_updated_at": "2026-01-01T00:00:00.000000Z"
      }
  ]
status:
  description: >
    The ZTP provisioning status string of the device.
    One of C(completed), C(unknown), or C(in_progress).
    Module fails if the device is not found.
  type: str
  returned: when state is status
  sample: "completed"
msg:
  description: Human-readable message describing the outcome.
  type: str
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


def _get_ztp_device_client(client_factory):
    """
    Get the base SDK client and return the ztp.device namespace.

    Falls back to None if the SDK does not support the ztp.device path,
    in which case the caller should use direct API calls.

    :param client_factory: The ApstraClientFactory instance.
    :return: A tuple of (base_client, ztp_device) or (base_client, None).
    """
    base_client = client_factory.get_base_client()

    # Try SDK approach first
    ztp_device = None
    try:
        ztp = getattr(base_client, "ztp", None)
        if ztp is not None:
            ztp_device = getattr(ztp, "device", None)
    except Exception:
        pass

    return base_client, ztp_device


def _sdk_list_devices(ztp_device):
    """List all ZTP devices using the SDK."""
    return ztp_device.list()


def _sdk_create_device(ztp_device, data):
    """Create a ZTP device using the SDK."""
    return ztp_device.create(data)


def _sdk_delete_device(ztp_device, ip_addr):
    """Delete a ZTP device using the SDK."""
    return ztp_device[ip_addr].delete()


def _sdk_get_device_status(ztp_device, ip_addr):
    """Get ZTP device status using the SDK."""
    return ztp_device[ip_addr].status()


def _api_list_devices(base_client, module):
    """List all ZTP devices using direct API calls."""
    module.debug("SDK ztp.device not available, using direct API for list")
    response = base_client._request(url="/api/ztp/device", method="GET")
    return response


def _api_create_device(base_client, module, data):
    """Create a ZTP device using direct API calls."""
    module.debug("SDK ztp.device not available, using direct API for create")
    response = base_client._request(url="/api/ztp/device", method="POST", data=data)
    return response


def _api_delete_device(base_client, module, ip_addr):
    """Delete a ZTP device using direct API calls."""
    module.debug("SDK ztp.device not available, using direct API for delete")
    base_client._request(url=f"/api/ztp/device/{ip_addr}", method="DELETE")


def _api_get_device_status(base_client, module, ip_addr):
    """Get ZTP device status using direct API calls."""
    module.debug("SDK ztp.device not available, using direct API for status")
    response = base_client._request(
        url=f"/api/ztp/device/{ip_addr}/status", method="GET"
    )
    return response


def _find_device_by_system_id(devices, system_id):
    """
    Find a device in the list of ZTP devices by system_id.

    :param devices: List of ZTP device dicts.
    :param system_id: The system_id to search for.
    :return: The matching device dict or None.
    """
    if devices is None:
        return None
    device_list = devices
    if isinstance(devices, dict):
        device_list = devices.get("items", list(devices.values()))
    if isinstance(device_list, list):
        for device in device_list:
            if isinstance(device, dict) and device.get("system_id") == system_id:
                return device
    return None


def _get_current_device(ztp_device, base_client, module, ip_addr, use_sdk):
    """
    Retrieve the current device state.

    The ZTP API does not support GET on individual devices, so we use
    the status endpoint to retrieve the device details.

    :param ztp_device: The SDK ztp.device namespace (or None).
    :param base_client: The base SDK client.
    :param module: The Ansible module.
    :param ip_addr: The device IP address.
    :param use_sdk: Whether to use the SDK.
    :return: The device dict or None if not found.
    """
    try:
        if use_sdk:
            return _sdk_get_device_status(ztp_device, ip_addr)
        else:
            return _api_get_device_status(base_client, module, ip_addr)
    except Exception:
        return None


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False, default=None),
        body=dict(type="dict", required=False, default=None),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent", "status"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        # Get the SDK ZTP device client (or fall back to direct API)
        base_client, ztp_device = _get_ztp_device_client(client_factory)
        use_sdk = ztp_device is not None

        # Validate params
        id = module.params.get("id", None) or {}
        body = module.params.get("body", None)
        state = module.params["state"]

        ip_addr = id.get("ip_addr", None)
        system_id = id.get("system_id", None)

        # If ip_addr not in id, check body for create operations
        if ip_addr is None and body is not None:
            ip_addr = body.get("ip_addr", None)

        # --- State: status ---
        if state == "status":
            if not ip_addr and not system_id:
                raise ValueError(
                    "Must specify 'ip_addr' or 'system_id' in 'id' to check device status."
                )

            # If we have system_id but no ip_addr, look up the IP from the device list
            if not ip_addr and system_id:
                if use_sdk:
                    devices = _sdk_list_devices(ztp_device)
                else:
                    devices = _api_list_devices(base_client, module)
                matched = _find_device_by_system_id(devices, system_id)
                if not matched:
                    module.fail_json(
                        msg=f"ZTP device with system_id '{system_id}' is not present.",
                        **result,
                    )
                    return
                ip_addr = matched.get("ip_addr")

            # Fetch status using the ip_addr
            if use_sdk:
                status_result = _sdk_get_device_status(ztp_device, ip_addr)
            else:
                status_result = _api_get_device_status(base_client, module, ip_addr)

            # The API returns None for non-existent devices — treat as not found
            if not status_result:
                lookup_desc = f"ip_addr '{ip_addr}'"
                if system_id:
                    lookup_desc = f"ip_addr '{ip_addr}' (system_id '{system_id}')"
                module.fail_json(
                    msg=f"ZTP device with {lookup_desc} is not present.",
                    **result,
                )
                return

            result["status"] = status_result.get("status", "unknown")
            result["ztp_device"] = status_result
            result["id"] = {"ip_addr": ip_addr}
            result["changed"] = False
            result["msg"] = "ZTP device status retrieved successfully"
            module.exit_json(**result)
            return

        # --- State: absent ---
        if state == "absent":
            if not ip_addr:
                raise ValueError(
                    "Must specify 'ip_addr' in 'id' to delete a ZTP device."
                )
            # Check if the device exists before deleting
            current_device = _get_current_device(
                ztp_device, base_client, module, ip_addr, use_sdk
            )
            if current_device:
                if use_sdk:
                    _sdk_delete_device(ztp_device, ip_addr)
                else:
                    _api_delete_device(base_client, module, ip_addr)
                result["changed"] = True
                result["msg"] = "ZTP device deleted successfully"
            else:
                result["changed"] = False
                result["msg"] = "ZTP device not found, nothing to delete"
            result["id"] = {"ip_addr": ip_addr}
            module.exit_json(**result)
            return

        # --- State: present ---
        # If no ip_addr and no body, list all devices
        if not ip_addr and not body:
            if use_sdk:
                devices = _sdk_list_devices(ztp_device)
            else:
                devices = _api_list_devices(base_client, module)
            result["ztp_devices"] = devices
            result["changed"] = False
            result["msg"] = "ZTP devices listed successfully"
            module.exit_json(**result)
            return

        # Check if the device currently exists (via status endpoint)
        current_device = None
        if ip_addr:
            current_device = _get_current_device(
                ztp_device, base_client, module, ip_addr, use_sdk
            )

        if current_device:
            # Device exists
            result["id"] = {"ip_addr": ip_addr}
            if body:
                # Check if there are differences
                changes = {}
                if client_factory.compare_and_update(current_device, body, changes):
                    # The ZTP device API does not support PUT/PATCH.
                    # Update by deleting and recreating with the new body.
                    if use_sdk:
                        _sdk_delete_device(ztp_device, ip_addr)
                        created_device = _sdk_create_device(ztp_device, body)
                    else:
                        _api_delete_device(base_client, module, ip_addr)
                        created_device = _api_create_device(base_client, module, body)
                    result["changed"] = True
                    if created_device:
                        result["response"] = created_device
                    result["changes"] = changes
                    result["msg"] = "ZTP device updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = "ZTP device already exists, no changes needed"
            else:
                result["changed"] = False
                result["msg"] = "No changes specified for ZTP device"

            # Return the final device state via status endpoint
            final_device = _get_current_device(
                ztp_device, base_client, module, ip_addr, use_sdk
            )
            if final_device:
                result["ztp_device"] = final_device
        else:
            # Device does not exist — create
            if body is None:
                raise ValueError("Must specify 'body' to create a ZTP device.")
            if use_sdk:
                created_device = _sdk_create_device(ztp_device, body)
            else:
                created_device = _api_create_device(base_client, module, body)

            # Determine the IP from the response or body
            created_ip = ip_addr
            if isinstance(created_device, dict):
                created_ip = created_device.get("ip_addr", created_ip)
            if created_ip:
                result["id"] = {"ip_addr": created_ip}

            result["changed"] = True
            result["response"] = created_device
            result["msg"] = "ZTP device created successfully"

            # Return the final device state via status endpoint
            if created_ip:
                final_device = _get_current_device(
                    ztp_device, base_client, module, created_ip, use_sdk
                )
                if final_device:
                    result["ztp_device"] = final_device

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
