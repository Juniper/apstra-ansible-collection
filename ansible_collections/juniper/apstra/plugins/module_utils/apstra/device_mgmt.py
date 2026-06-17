# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Utility helpers for the device_management module.

Public API
----------
get_agent_status(client_factory, agent_id) -> dict
reboot_device(client_factory, agent_id, force=False) -> None
wait_for_agent_online(client_factory, agent_id, timeout) -> str
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import time


# ---------------------------------------------------------------------------
# Agent status
# ---------------------------------------------------------------------------


def get_agent_status(client_factory, agent_id):
    """Return the flattened status dict for a system agent.

    Merges ``status`` sub-key fields into the returned dict so callers can
    access ``connection_state``, ``system_id``, and ``management_level``
    directly.

    :param client_factory: ApstraClientFactory instance.
    :param agent_id: Global system-agent UUID.
    :returns: dict with agent fields.
    :raises RuntimeError: if the agent cannot be retrieved.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/system-agents/{agent_id}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to retrieve system agent '{agent_id}': "
            f"HTTP {resp.status_code} — {resp.text}"
        )
    agent = resp.json()
    # Flatten status sub-key so callers don't need to navigate nested dict
    status = agent.get("status") or {}
    flat = {**agent, **status}
    return flat


# ---------------------------------------------------------------------------
# Reboot
# ---------------------------------------------------------------------------


def reboot_device(client_factory, agent_id, force=False):
    """Trigger a reboot of the device associated with *agent_id*.

    :param client_factory: ApstraClientFactory instance.
    :param agent_id: Global system-agent UUID.
    :param force: When True, reboot even if the device is in a blueprint.
    :raises RuntimeError: if the reboot request fails.
    """
    base = client_factory.get_base_client()
    # SDK method: base.system_agents[agent_id].reboot(force=force)
    # Which maps to POST /api/system-agents/{id}/reboot?force=<bool>
    force_val = "true" if force else "false"
    resp = base.raw_request(
        f"/system-agents/{agent_id}/reboot",
        method="POST",
        params={"force": force_val},
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise RuntimeError(
            f"Failed to reboot device agent '{agent_id}': "
            f"HTTP {resp.status_code} — {resp.text}"
        )


# ---------------------------------------------------------------------------
# Wait for reconnection
# ---------------------------------------------------------------------------

_POLL_INTERVAL = 10  # seconds between connection_state checks


def wait_for_agent_online(client_factory, agent_id, timeout):
    """Poll until the agent reconnects or *timeout* is exceeded.

    :param client_factory: ApstraClientFactory instance.
    :param agent_id: Global system-agent UUID.
    :param timeout: Maximum number of seconds to wait.
    :returns: Final ``connection_state`` string (e.g. ``"connected"``).
    """
    deadline = time.time() + timeout
    # Give the device a moment to begin its reboot cycle before we start
    # polling — if we poll immediately we might still see "connected".
    time.sleep(15)

    while time.time() < deadline:
        try:
            status = get_agent_status(client_factory, agent_id)
            state = status.get("connection_state", "")
            if state == "connected":
                return state
        except Exception:
            # Transient failures during reboot are expected — keep polling
            pass
        time.sleep(_POLL_INTERVAL)

    # Return last known state (or empty string)
    try:
        return get_agent_status(client_factory, agent_id).get("connection_state", "")
    except Exception:
        return ""
