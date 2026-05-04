#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: system_agents

short_description: Manage system agents (device onboarding) in Apstra

version_added: "0.2.0"

author:
  - "Vamsi Gavini (@vgavini)"

description:
  - This module manages system agents in Apstra for onboarding and managing
    network devices.
  - Supports creating (onboarding), updating, and deleting system agents.
  - Uses the Apstra system-agents API via the AOS SDK.
  - Provides full idempotency. Agents are matched by C(management_ip) or
    C(agent_id) to prevent duplicates.
  - After onboarding, the agent connection state can be checked to confirm
    the device is reachable and authenticated.

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
      - The Apstra username for authentication.
    type: str
    required: false
  password:
    description:
      - The Apstra password for authentication.
    type: str
    required: false
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  id:
    description:
      - A dict identifying an existing system agent.
      - Not required for C(state=gathered).
    required: false
    type: dict
    suboptions:
      agent_id:
        description:
          - The ID of an existing system agent.
          - Required for update and delete operations when
            C(management_ip) is not specified in C(body).
        type: str
        required: false
  body:
    description:
      - A dict containing the system agent specification.
    required: false
    type: dict
    suboptions:
      management_ip:
        description:
          - The management IP address or hostname of the device to onboard.
          - Used to create a new agent and for idempotent matching of
            existing agents.
        type: str
        required: false
      agent_type:
        description:
          - The type of system agent.
          - C(offbox) runs the agent in an Apstra-managed container.
          - C(onbox) installs the agent directly on the device.
        type: str
        required: false
        choices: ["offbox", "onbox"]
        default: "offbox"
      label:
        description:
          - A human-readable label for the system agent.
        type: str
        required: false
      operation_mode:
        description:
          - The operation mode for the agent.
          - C(full_control) allows Apstra to manage the device configuration.
        type: str
        required: false
        choices: ["full_control"]
        default: "full_control"
      device_username:
        description:
          - The username for authenticating to the managed device.
        type: str
        required: false
      device_password:
        description:
          - The password for authenticating to the managed device.
        type: str
        required: false
      platform:
        description:
          - The device platform/OS family.
          - Required when creating an agent without a C(profile).
        type: str
        required: false
        choices: ["junos", "eos", "nxos"]
      profile:
        description:
          - The system agent profile ID to use.
        type: str
        required: false
      job_on_create:
        description:
          - Action to trigger automatically when the agent is created.
          - C(check) validates device reachability; C(install) deploys the agent.
        type: str
        required: false
        choices: ["check", "install"]
      open_options:
        description:
          - Device driver options passed to the agent.
        type: dict
        required: false
      force_package_install:
        description:
          - Force reinstallation of agent packages.
        type: bool
        required: false
        default: false
      wait_for_connection:
        description:
          - If true, wait for the agent to reach C(connected) state after
            creation or update.
        type: bool
        required: false
        default: false
      wait_timeout:
        description:
          - Maximum time in seconds to wait for the agent to connect.
        type: int
        required: false
        default: 120
  state:
    description:
      - Desired state of the system agent.
      - C(present) will create or update the agent.
      - C(absent) will uninstall the agent container (if running) and then
        delete the agent. The uninstall job runs asynchronously; the module
        waits up to C(uninstall_timeout) seconds for it to complete before
        issuing the delete.
      - C(gathered) lists all agents and returns their details
        including system_id (device serial number). Useful for
        building device-to-serial mappings without raw API calls.
      - C(installed) triggers install-agent on agents whose containers
        are not yet running. Accepts C(body.wait_for_connection) and
        C(body.wait_timeout) to poll until all agents reach connected.
      - C(acknowledged) discovers unacknowledged (OOS-QUARANTINED)
        systems and approves them (sets admin_state=normal) so they
        become OOS-READY for blueprint assignment.
      - When C(state=acknowledged) and C(body.management_ip) is provided,
        only the device matching that IP will be acknowledged. Without
        C(management_ip), all unacknowledged devices are acknowledged.
    type: str
    required: false
    choices: ["present", "absent", "gathered", "installed", "acknowledged"]
    default: "present"
  uninstall_timeout:
    description:
      - Maximum time in seconds to wait for the uninstall job to finish
        before attempting to delete the agent.
      - Only used when C(state=absent) and the agent container is running.
    type: int
    required: false
    default: 120
"""

EXAMPLES = """
# ── Onboard a device (offbox agent) ───────────────────────────────

- name: Onboard a Junos switch
  juniper.apstra.system_agents:
    body:
      management_ip: "10.0.0.1"
      agent_type: "offbox"
      label: "spine-1"
      operation_mode: "full_control"
      device_username: "admin"
      device_password: "admin@123"
      job_on_create: "check"
    state: present
  register: agent

# ── Onboard with platform hint ────────────────────────────────────

- name: Onboard an EOS switch
  juniper.apstra.system_agents:
    body:
      management_ip: "10.0.0.2"
      agent_type: "offbox"
      label: "leaf-1"
      device_username: "admin"
      device_password: "Arista123"
      platform: "eos"
    state: present

# ── Update agent label ────────────────────────────────────────────

- name: Update agent label
  juniper.apstra.system_agents:
    id:
      agent_id: "{{ agent.agent_id }}"
    body:
      label: "spine-1-updated"
    state: present

# ── Delete an agent ───────────────────────────────────────────────

- name: Delete system agent
  juniper.apstra.system_agents:
    id:
      agent_id: "{{ agent.agent_id }}"
    state: absent

# ── Delete agent by management IP ─────────────────────────────────

- name: Delete system agent by IP
  juniper.apstra.system_agents:
    body:
      management_ip: "10.0.0.1"
    state: absent

# ── Onboard and wait for connection ───────────────────────────────

- name: Onboard and wait for device to connect
  juniper.apstra.system_agents:
    body:
      management_ip: "10.0.0.3"
      agent_type: "offbox"
      label: "leaf-2"
      device_username: "admin"
      device_password: "admin@123"
      wait_for_connection: true
      wait_timeout: 180
    state: present

# ── List all agents (gather serial numbers) ───────────────────────

- name: Gather all system agents
  juniper.apstra.system_agents:
    state: gathered
  register: all_agents

- name: Build label-to-serial map
  ansible.builtin.set_fact:
    serial_map: >-
      {{ dict(all_agents.agents
         | selectattr('system_id')
         | map(attribute='label')
         | zip(all_agents.agents
               | selectattr('system_id')
               | map(attribute='system_id'))
         | list) }}
# ── Trigger install-agent + wait for all agents to connect ────

- name: Install agents and wait for connection
  juniper.apstra.system_agents:
    body:
      wait_for_connection: true
      wait_timeout: 180
    state: installed
  register: install_result

# ── Acknowledge unacknowledged devices ────────────────────────

- name: Acknowledge all quarantined devices
  juniper.apstra.system_agents:
    state: acknowledged
  register: ack_result

# ── Acknowledge a single device by management IP ─────────────

- name: Acknowledge one device by IP
  juniper.apstra.system_agents:
    body:
      management_ip: "10.0.0.1"
    state: acknowledged
  register: ack_one
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
agent_id:
  description: The ID of the system agent.
  type: str
  returned: on create or when agent is found
management_ip:
  description: The management IP of the agent.
  type: str
  returned: when agent exists
system_id:
  description: The system ID of the managed device (once acknowledged).
  type: str
  returned: when device is acknowledged
connection_state:
  description: The connection state of the agent.
  type: str
  returned: when agent exists
  sample: "connected"
agent:
  description: Full agent details from the API.
  type: dict
  returned: when agent exists
agents:
  description:
    - List of all system agents with their details.
    - Only returned when C(state=gathered).
    - Each entry contains agent_id, label, management_ip,
      system_id, and connection_state.
  type: list
  elements: dict
  returned: when state=gathered
  sample:
    - agent_id: "abc-123"
      label: "spine-1"
      management_ip: "10.0.0.1"
      system_id: "SERIAL123"
      connection_state: "connected"
msg:
  description: The output message that the module generates.
  type: str
  returned: always
installed_agents:
  description:
    - List of agent IDs that had install-agent triggered.
    - Only returned when C(state=installed).
  type: list
  elements: str
  returned: when state=installed
acknowledged_systems:
  description:
    - List of device_key values that were acknowledged.
    - Only returned when C(state=acknowledged).
  type: list
  elements: str
  returned: when state=acknowledged
"""

import traceback
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


# ──────────────────────────────────────────────────────────────────
#  SDK helpers
# ──────────────────────────────────────────────────────────────────


def _get_base_client(client_factory):
    """Return the base AOS SDK client."""
    return client_factory.get_base_client()


def _list_agents(client_factory):
    """GET /api/system-agents — list all system agents."""
    client = _get_base_client(client_factory)
    result = client.system_agents.list()
    # The SDK's RestResources.list() already extracts the 'items' list
    # from the API response, so result is a list (or None).
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "items" in result:
        return result["items"]
    return []


def _get_agent(client_factory, agent_id):
    """GET /api/system-agents/{id} — get a single agent."""
    client = _get_base_client(client_factory)
    try:
        return client.system_agents[agent_id].get()
    except Exception:
        return None


def _create_agent(client_factory, data):
    """POST /api/system-agents — create a new system agent."""
    client = _get_base_client(client_factory)
    return client.system_agents.create(data)


def _update_agent(client_factory, agent_id, data):
    """PUT /api/system-agents/{id} — update an existing agent."""
    client = _get_base_client(client_factory)
    return client.system_agents[agent_id].update(data)


def _delete_agent(client_factory, agent_id):
    """DELETE /api/system-agents/{id} — delete an agent."""
    client = _get_base_client(client_factory)
    return client.system_agents[agent_id].delete()


def _uninstall_agent(client_factory, agent_id):
    """POST /api/system-agents/{id}/uninstall-agent — stop the agent container."""
    client = _get_base_client(client_factory)
    return client.system_agents[agent_id].uninstall()


def _is_container_running(agent):
    """Return True if the agent's offbox container is currently running."""
    container_status = agent.get("container_status", {})
    return container_status.get("status", "") == "running"


def _wait_for_uninstall(client_factory, agent_id, timeout):
    """Wait until the agent container stops running (uninstall complete)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        agent = _get_agent(client_factory, agent_id)
        if agent is None:
            # Agent already gone — nothing to wait for
            return
        if not _is_container_running(agent):
            # Container stopped — check if uninstall job completed
            last_job = agent.get("last_job_status", {})
            job_state = last_job.get("state", "")
            if job_state in ("success", "error", ""):
                return
        time.sleep(10)
    raise TimeoutError(
        f"Agent {agent_id} container did not stop within {timeout}s after uninstall"
    )


def _find_agent_by_ip(client_factory, management_ip):
    """Find an existing agent by management IP address.

    The Apstra API may return the management_ip at the top level of the
    agent object or nested under a ``config`` dict.  Check both locations
    so lookup succeeds regardless of the response format.
    """
    agents = _list_agents(client_factory)
    for agent in agents:
        # Top-level field (common in Apstra 4.x+)
        if agent.get("management_ip") == management_ip:
            return agent
        # Nested under config (older responses / alternative format)
        config = agent.get("config", {})
        if config.get("management_ip") == management_ip:
            return agent
    return None


def _build_create_body(params):
    """Build the POST body for creating a system agent."""
    body = {
        "management_ip": params["management_ip"],
        "agent_type": params.get("agent_type", "offbox"),
    }

    if params.get("label"):
        body["label"] = params["label"]

    if params.get("operation_mode"):
        body["operation_mode"] = params["operation_mode"]

    if params.get("device_username"):
        body["username"] = params["device_username"]

    if params.get("device_password"):
        body["password"] = params["device_password"]

    if params.get("platform"):
        body["platform"] = params["platform"]

    if params.get("profile"):
        body["profile"] = params["profile"]

    if params.get("job_on_create"):
        body["job_on_create"] = params["job_on_create"]

    if params.get("open_options"):
        body["open_options"] = params["open_options"]

    if params.get("force_package_install"):
        body["force_package_install"] = params["force_package_install"]

    return body


def _build_update_body(params):
    """Build the PUT body for updating a system agent.

    The PUT endpoint replaces the mutable configuration fields, so all
    required fields must be included.  The caller is expected to merge
    existing config values into *params* before calling this function.

    Note: ``management_ip`` and ``agent_type`` are immutable after
    creation and must NOT be included in the PUT body.
    """
    body = {}

    if params.get("label") is not None:
        body["label"] = params["label"]

    if params.get("operation_mode") is not None:
        body["operation_mode"] = params["operation_mode"]

    if params.get("device_username") is not None:
        body["username"] = params["device_username"]

    if params.get("device_password") is not None:
        body["password"] = params["device_password"]

    if params.get("platform") is not None:
        body["platform"] = params["platform"]

    if params.get("open_options") is not None:
        body["open_options"] = params["open_options"]

    if params.get("force_package_install"):
        body["force_package_install"] = params["force_package_install"]

    return body


def _needs_update(existing, params):
    """Check if the existing agent needs updating based on provided params."""
    config = existing.get("config", {})
    changes = {}

    if params.get("label") is not None and config.get("label") != params["label"]:
        changes["label"] = params["label"]

    if (
        params.get("operation_mode") is not None
        and config.get("operation_mode") != params["operation_mode"]
    ):
        changes["operation_mode"] = params["operation_mode"]

    if (
        params.get("platform") is not None
        and config.get("platform") != params["platform"]
    ):
        changes["platform"] = params["platform"]

    # Credentials can't be compared (not returned by API), so skip them
    # unless explicitly provided (forces an update)
    if params.get("device_username") is not None:
        if config.get("username") != params["device_username"]:
            changes["username"] = params["device_username"]

    return changes


def _build_result(agent, changed, msg):
    """Build the standard result dict from an agent response."""
    result = dict(changed=changed, msg=msg)

    if agent:
        result["agent_id"] = agent.get("id", "")
        config = agent.get("config", {})
        result["management_ip"] = config.get("management_ip", "")
        status = agent.get("status", {})
        result["system_id"] = status.get("system_id", "")
        result["connection_state"] = status.get("connection_state", "")
        result["agent"] = agent

    return result


def _wait_for_connection(client_factory, agent_id, timeout):
    """Wait for agent to reach connected state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        agent = _get_agent(client_factory, agent_id)
        if agent:
            status = agent.get("status", {})
            state = status.get("connection_state", "")
            if state == "connected":
                return agent
            if state == "auth_failed":
                raise ValueError(
                    f"Agent {agent_id} authentication failed: "
                    f"{status.get('status_message', '')}"
                )
        time.sleep(10)
    raise TimeoutError(
        f"Agent {agent_id} did not reach 'connected' state within {timeout}s"
    )


# ──────────────────────────────────────────────────────────────────
#  State handlers
# ──────────────────────────────────────────────────────────────────


def _handle_present(module, client_factory):
    """Handle state=present — create or update."""
    id_param = module.params.get("id") or {}
    body = module.params.get("body") or {}
    p = {**id_param, **body}  # merge for helper functions
    agent_id = id_param.get("agent_id")
    management_ip = body.get("management_ip")
    wait = body.get("wait_for_connection", False)
    wait_timeout = body.get("wait_timeout", 120)

    # Find existing agent
    existing = None
    if agent_id:
        existing = _get_agent(client_factory, agent_id)
    elif management_ip:
        existing = _find_agent_by_ip(client_factory, management_ip)
        if existing:
            agent_id = existing["id"]

    if existing:
        # UPDATE path
        changes = _needs_update(existing, p)
        if not changes:
            agent = existing
            if wait:
                agent = _wait_for_connection(client_factory, agent_id, wait_timeout)
            return _build_result(agent, False, "system agent already up to date")

        # Carry over existing config fields that are required by the PUT endpoint
        # but not specified by the user (e.g. platform, operation_mode, username).
        # Note: management_ip and agent_type are immutable after creation and
        # are not accepted by the PUT endpoint.
        existing_config = existing.get("config", {})
        carry_over_fields = {
            "platform": "platform",
            "operation_mode": "operation_mode",
            "device_username": "username",
        }
        for param_key, config_key in carry_over_fields.items():
            if not p.get(param_key) and existing_config.get(config_key):
                p[param_key] = existing_config[config_key]

        update_body = _build_update_body(p)
        _update_agent(client_factory, agent_id, update_body)
        agent = _get_agent(client_factory, agent_id)

        if wait:
            agent = _wait_for_connection(client_factory, agent_id, wait_timeout)

        return _build_result(agent, True, "system agent updated successfully")
    else:
        # CREATE path
        if not management_ip:
            raise ValueError("management_ip is required to create a new system agent")

        if not p.get("platform") and not p.get("profile"):
            raise ValueError(
                "'platform' (or 'profile') is required when creating a new "
                "system agent. Supported platforms: junos, eos, nxos"
            )

        create_body = _build_create_body(p)
        try:
            response = _create_agent(client_factory, create_body)
        except Exception as exc:
            # Handle 409 Conflict — agent already exists (race or stale cache)
            exc_str = str(exc)
            if "409" in exc_str or "already" in exc_str.lower():
                # Try to extract agent ID from the error message
                # Format: "ip X.X.X.X already used by offbox agent: <uuid>"
                import re as _re

                id_match = _re.search(r"agent:\s*([0-9a-f-]{36})", exc_str)
                existing = None
                if id_match:
                    existing = _get_agent(client_factory, id_match.group(1))
                if not existing:
                    existing = _find_agent_by_ip(client_factory, management_ip)
                if existing:
                    agent_id = existing["id"]
                    if wait:
                        existing = _wait_for_connection(
                            client_factory, agent_id, wait_timeout
                        )
                    return _build_result(
                        existing,
                        False,
                        "system agent already exists (409 conflict resolved)",
                    )
            raise

        agent_id = response.get("id") if isinstance(response, dict) else None

        if not agent_id:
            raise ValueError(
                "System agent was created but no ID was returned. "
                "Check the Apstra system agents list."
            )

        agent = _get_agent(client_factory, agent_id)

        if wait:
            agent = _wait_for_connection(client_factory, agent_id, wait_timeout)

        return _build_result(agent, True, "system agent created successfully")


def _handle_gathered(module, client_factory):
    """Handle state=gathered — list all agents."""
    agents = _list_agents(client_factory)

    result_agents = []
    for agent in agents:
        config = agent.get("config", {})
        status = agent.get("status", {})
        result_agents.append(
            {
                "agent_id": agent.get("id", ""),
                "label": config.get("label", ""),
                "management_ip": config.get("management_ip", ""),
                "system_id": status.get("system_id", ""),
                "connection_state": status.get("connection_state", ""),
                "agent_type": config.get("agent_type", ""),
                "operation_mode": config.get("operation_mode", ""),
                "platform": config.get("platform", ""),
            }
        )

    return dict(
        changed=False,
        agents=result_agents,
        msg=f"gathered {len(result_agents)} system agent(s)",
    )


def _handle_installed(module, client_factory):
    """Handle state=installed — trigger install-agent for non-running agents.

    1. Lists all agents via the SDK.
    2. For each agent whose container_status.status != 'running',
       POST /api/system-agents/{id}/install-agent (409 = already running, OK).
    3. If body.wait_for_connection is true, polls until all agents are connected.

    Returns the list of agent IDs that had install triggered.
    """
    body = module.params.get("body") or {}
    wait = body.get("wait_for_connection", False)
    wait_timeout = body.get("wait_timeout", 180)

    base = _get_base_client(client_factory)
    agents = _list_agents(client_factory)

    # Find agents that need install
    need_install = []
    for agent in agents:
        container = agent.get("container_status", {})
        if container.get("status") != "running":
            need_install.append(agent.get("id"))

    # Trigger install-agent for each
    installed = []
    for agent_id in need_install:
        try:
            base.raw_request(
                f"/system-agents/{agent_id}/install-agent",
                "POST",
                data={},
            )
            installed.append(agent_id)
        except Exception as exc:
            # 409 = already running an install job — that's fine
            if "409" in str(exc):
                installed.append(agent_id)
            else:
                raise

    changed = len(installed) > 0

    # Optionally wait for all agents to connect
    if wait:
        deadline = time.time() + wait_timeout
        while time.time() < deadline:
            current = _list_agents(client_factory)
            not_connected = [
                a.get("id")
                for a in current
                if a.get("status", {}).get("connection_state") != "connected"
            ]
            if not not_connected:
                break
            time.sleep(15)
        else:
            # Timed out — gather final state for reporting
            current = _list_agents(client_factory)
            not_connected = [
                a.get("config", {}).get("label", a.get("id"))
                for a in current
                if a.get("status", {}).get("connection_state") != "connected"
            ]
            if not_connected:
                raise TimeoutError(
                    f"Agents not connected after {wait_timeout}s: " f"{not_connected}"
                )

    # Gather final agent summary
    final_agents = _list_agents(client_factory)
    result_agents = []
    for agent in final_agents:
        config = agent.get("config", {})
        status = agent.get("status", {})
        result_agents.append(
            {
                "agent_id": agent.get("id", ""),
                "label": config.get("label", ""),
                "management_ip": config.get("management_ip", ""),
                "system_id": status.get("system_id", ""),
                "connection_state": status.get("connection_state", ""),
            }
        )

    return dict(
        changed=changed,
        installed_agents=installed,
        agents=result_agents,
        msg=(
            f"install-agent triggered for {len(installed)} agent(s), "
            f"{len(result_agents)} total"
        ),
    )


def _handle_acknowledged(module, client_factory):
    """Handle state=acknowledged — acknowledge unacknowledged devices.

    1. GET /api/systems — list all systems.
    2. Find systems where status.is_acknowledged == false.
    3. If ``body.management_ip`` is provided, filter to only the device
       whose ``facts.mgmt_ipaddr`` matches that IP.
    4. PUT /api/systems/{device_key} with admin_state=normal.

    Returns the list of device_keys that were acknowledged.
    """
    body = module.params.get("body") or {}
    target_ip = body.get("management_ip")
    base = _get_base_client(client_factory)

    # List all systems
    resp = base.raw_request("/systems")
    if resp.status_code != 200:
        raise Exception(f"GET /systems failed: {resp.status_code} {resp.text}")
    try:
        systems_data = resp.json()
    except Exception:
        systems_data = {}
    all_systems = systems_data.get("items", [])

    # Find unacknowledged
    need_ack = [
        s for s in all_systems if not s.get("status", {}).get("is_acknowledged", True)
    ]

    # If a specific management IP was requested, filter to that device
    if target_ip:
        need_ack = [
            s for s in need_ack if s.get("facts", {}).get("mgmt_ipaddr") == target_ip
        ]
        if not need_ack:
            # Check if the device exists but is already acknowledged
            already = [
                s
                for s in all_systems
                if s.get("facts", {}).get("mgmt_ipaddr") == target_ip
                and s.get("status", {}).get("is_acknowledged", False)
            ]
            if already:
                return dict(
                    changed=False,
                    acknowledged_systems=[],
                    msg=f"Device {target_ip} is already acknowledged",
                )
            return dict(
                changed=False,
                acknowledged_systems=[],
                msg=f"No unacknowledged device found with IP {target_ip}",
            )

    acknowledged = []
    for system in need_ack:
        device_key = system.get("device_key")
        if not device_key:
            continue
        facts = system.get("facts", {})
        ack_body = {
            "user_config": {
                "admin_state": "normal",
                "aos_hcl_model": facts.get("aos_hcl_model", ""),
            }
        }
        resp = base.raw_request(f"/systems/{device_key}", "PUT", data=ack_body)
        if resp.status_code == 200:
            acknowledged.append(device_key)

    return dict(
        changed=len(acknowledged) > 0,
        acknowledged_systems=acknowledged,
        msg=(
            f"{len(acknowledged)} device(s) acknowledged out of "
            f"{len(need_ack)} unacknowledged"
        ),
    )


def _handle_absent(module, client_factory):
    """Handle state=absent — uninstall container if running, then delete."""
    id_param = module.params.get("id") or {}
    body = module.params.get("body") or {}
    agent_id = id_param.get("agent_id")
    management_ip = body.get("management_ip")
    uninstall_timeout = module.params.get("uninstall_timeout") or 120

    # Find the agent
    existing = None
    if not agent_id and management_ip:
        existing = _find_agent_by_ip(client_factory, management_ip)
        if existing:
            agent_id = existing["id"]

    if not agent_id:
        return dict(changed=False, msg="system agent not found (nothing to delete)")

    # Refresh agent info if not already fetched
    if existing is None:
        existing = _get_agent(client_factory, agent_id)
    if not existing:
        return dict(changed=False, msg="system agent not found (nothing to delete)")

    # Uninstall the container first if it is still running
    if _is_container_running(existing):
        _uninstall_agent(client_factory, agent_id)
        _wait_for_uninstall(client_factory, agent_id, uninstall_timeout)

    _delete_agent(client_factory, agent_id)
    return dict(
        changed=True, msg="system agent deleted successfully", agent_id=agent_id
    )


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent", "gathered", "installed", "acknowledged"],
            default="present",
        ),
        uninstall_timeout=dict(type="int", required=False, default=120),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        state = module.params["state"]
        if state == "present":
            result = _handle_present(module, client_factory)
        elif state == "absent":
            result = _handle_absent(module, client_factory)
        elif state == "gathered":
            result = _handle_gathered(module, client_factory)
        elif state == "installed":
            result = _handle_installed(module, client_factory)
        elif state == "acknowledged":
            result = _handle_acknowledged(module, client_factory)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
