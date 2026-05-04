# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Shared helpers for Apstra OS-upgrade operations.

Used by ``os_upgrade`` (single device) and the forthcoming
``upgrade_group`` modules.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
import time

# ---------------------------------------------------------------------------
# UUID helper
# ---------------------------------------------------------------------------

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_uuid(value):
    """Return True if *value* looks like an Apstra UUID."""
    return bool(_UUID_RE.match(value or ""))


# ---------------------------------------------------------------------------
# System-agent resolution
# ---------------------------------------------------------------------------


def list_global_agents(client_factory):
    """Return all items from ``GET /api/system-agents``."""
    base = client_factory.get_base_client()
    result = base.system_agents.list()
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "items" in result:
        return result["items"]
    return []


def _build_system_id_to_agent_map(client_factory):
    """Build a dict mapping ``status.system_id`` → global agent UUID.

    Agent labels in Apstra are optional and often empty; the ``system_id``
    (device serial / MAC) is the reliable cross-reference between the
    blueprint graph and the global ``/system-agents`` resource.
    """
    agents = list_global_agents(client_factory)
    return {
        a.get("status", {}).get("system_id"): a.get("id")
        for a in agents
        if a.get("status", {}).get("system_id")
    }


def list_blueprint_system_info(client_factory, blueprint_id):
    """Return all device records from
    ``GET /blueprints/{bp}/experience/web/system-info``.

    Each record contains ``label``, ``system_id`` (may be None for
    unassigned nodes), ``role``, ``hostname``, etc.
    Only records with a non-null ``system_id`` are assigned to real devices.
    """
    base = client_factory.get_base_client()
    try:
        resp = base.raw_request(
            f"/blueprints/{blueprint_id}/experience/web/system-info"
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        # The endpoint returns {"data": [...], "version": ...}
        items = data.get("data", data) if isinstance(data, dict) else data
        return items if isinstance(items, list) else []
    except Exception:
        return []


def resolve_agent_id(client_factory, system_ref, blueprint_id=None):
    """Resolve *system_ref* to a global system-agent UUID.

    Resolution order (first match wins):

    1. Direct UUID match against ``/system-agents`` item ``id``.
    2. Management-IP match against ``config.management_ip``.
    3. Label match against ``config.label`` (empty on many Apstra installs).
    4. ``system_id`` (device serial/MAC) match against ``status.system_id``.
    5. Blueprint-node label lookup via
       ``/blueprints/{bp}/experience/web/system-info``
       (requires *blueprint_id*; resolves human-readable names like
       ``apstra_esi_001_leaf1`` that are not stored in the global agent).

    Raises ``ValueError`` if not found.
    """
    if not system_ref:
        raise ValueError("'id.system' is required to identify a system agent")

    agents = list_global_agents(client_factory)

    # Steps 1–4: direct lookup in global /system-agents
    for agent in agents:
        agent_id = agent.get("id", "")
        config = agent.get("config", {})
        status = agent.get("status", {})
        label = config.get("label", "")
        mgmt_ip = config.get("management_ip", "")
        sys_id = status.get("system_id", "")

        if (
            agent_id == system_ref
            or mgmt_ip == system_ref
            or (label and label == system_ref)
            or (sys_id and sys_id == system_ref)
        ):
            return agent_id

    # Step 5: blueprint-node label → system_id → agent_id
    if blueprint_id:
        sys_to_agent = _build_system_id_to_agent_map(client_factory)
        sys_info = list_blueprint_system_info(client_factory, blueprint_id)
        for node in sys_info:
            node_label = node.get("label", "")
            node_sys_id = node.get("system_id")
            if node_label == system_ref and node_sys_id:
                agent_id = sys_to_agent.get(node_sys_id)
                if agent_id:
                    return agent_id

    raise ValueError(
        f"System agent not found for '{system_ref}'. "
        "Provide an agent UUID, device label, management IP, or system_id."
    )


def get_global_agent(client_factory, agent_id):
    """Return a single system-agent dict from ``GET /api/system-agents/{id}``."""
    base = client_factory.get_base_client()
    try:
        return base.system_agents[agent_id].get()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# OS image resolution (blueprint-scoped)
# ---------------------------------------------------------------------------


def list_blueprint_images(client_factory, blueprint_id=None):
    """Return all OS images from ``GET /device-os/images`` (global).

    In Apstra 6.1+, OS images are managed globally at ``/device-os/images``.
    The blueprint-scoped path (``/blueprints/{bp}/device-os/images``) returns
    404 on 6.1.1 and is not used.

    The *blueprint_id* parameter is accepted for API compatibility but
    currently has no effect.
    """
    base = client_factory.get_base_client()
    try:
        resp = base.raw_request("/device-os/images")
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return []


def resolve_image_id(client_factory, blueprint_id, image_ref):
    """Resolve *image_ref* to an OS-image UUID.

    *image_ref* may be:
    - An image UUID (returned as-is)
    - An image name (``image_name`` field, e.g. the .tgz/.iso filename)
    - An image description (``description`` field)
    - Legacy ``filename`` or ``label`` fields (for older API versions)

    Raises ``ValueError`` if not found.
    """
    if not image_ref:
        raise ValueError("'body.image' is required to identify an OS image")

    if is_uuid(image_ref):
        return image_ref

    images = list_blueprint_images(client_factory, blueprint_id)
    for image in images:
        img_id = image.get("id", "")
        # 6.1+ fields
        image_name = image.get("image_name", "")
        description = image.get("description", "")
        # Legacy fields (older API versions)
        filename = image.get("filename", "")
        label = image.get("label", "")
        if (
            image_ref == image_name
            or image_ref == description
            or image_ref == filename
            or image_ref == label
            or image_ref == img_id
        ):
            return img_id

    # Build a helpful list of available images for the error message
    available = [
        image.get("image_name") or image.get("filename") or image.get("id", "?")
        for image in images
    ]
    raise ValueError(
        f"OS image not found for '{image_ref}'. "
        f"Available images: {available}. "
        "Provide an image UUID, image_name, or description."
    )


# ---------------------------------------------------------------------------
# Blueprint system-agents (list)
# ---------------------------------------------------------------------------


def list_blueprint_agent_ids(client_factory, blueprint_id):
    """Return the global agent UUIDs for all assigned devices in *blueprint_id*.

    The blueprint-scoped ``/blueprints/{bp}/system-agents`` endpoint is not
    available in all Apstra versions (returns 404 on 6.1.1).  Instead:

    1. ``GET /blueprints/{bp}/experience/web/system-info`` → nodes with
       ``system_id`` populated (i.e. real devices, not unassigned nodes).
    2. Map each ``system_id`` → global agent UUID via ``/system-agents``.
    """
    sys_info = list_blueprint_system_info(client_factory, blueprint_id)
    assigned = [n.get("system_id") for n in sys_info if n.get("system_id")]
    if not assigned:
        return []

    sys_to_agent = _build_system_id_to_agent_map(client_factory)
    agent_ids = [sys_to_agent[sid] for sid in assigned if sid in sys_to_agent]
    return agent_ids


# ---------------------------------------------------------------------------
# Upgrade trigger
# ---------------------------------------------------------------------------


def trigger_upgrade(client_factory, blueprint_id, agent_id, image_id):
    """POST ``/system-agents/{agent_id}/dos-upgrade`` (global path).

    In Apstra 6.1.1 the upgrade API is rooted at the global
    ``/system-agents`` resource, not the blueprint-scoped path.
    The *blueprint_id* parameter is kept for interface compatibility.

    Returns the API response dict (may contain a job reference).
    """
    base = client_factory.get_base_client()
    return base.system_agents[agent_id].dos_upgrade(image_id=image_id)


# ---------------------------------------------------------------------------
# Upgrade impact report
# ---------------------------------------------------------------------------


def get_upgrade_impact(client_factory, blueprint_id, agent_ids):
    """POST ``/system-agents/upgrade-impact`` (global path).

    In Apstra 6.1.1 the upgrade-impact API is at the global
    ``/system-agents/upgrade-impact`` endpoint (not blueprint-scoped).
    The endpoint returns HTTP 202 on success.

    The request body uses ``{"system_agents": [agent_ids]}`` — the field
    name differs from the SDK schema (which uses ``agent_ids``).

    *blueprint_id* is kept for interface compatibility but is not used.

    Returns the impact-report response dict from the API.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        "/system-agents/upgrade-impact",
        "POST",
        data={"system_agents": agent_ids},
    )
    if resp.status_code not in (200, 202):
        raise Exception(
            f"upgrade-impact failed: HTTP {resp.status_code} — {resp.text[:400]}"
        )
    return resp.json()


# ---------------------------------------------------------------------------
# Job status polling
# ---------------------------------------------------------------------------

# Terminal job states returned by Apstra
_TERMINAL_STATES = frozenset({"success", "error", "failed"})
# States that indicate a job is actively running
_ACTIVE_STATES = frozenset({"in_progress", "running", "init", "pending"})
# Default seconds between polls
_DEFAULT_POLL_INTERVAL = 15


def wait_for_upgrade_job(client_factory, blueprint_id, agent_id, timeout):
    """Poll until the agent's upgrade job reaches a terminal state.

    Polls ``GET /api/system-agents/{agent_id}`` every
    ``_DEFAULT_POLL_INTERVAL`` seconds and reads ``last_job_status.state``.

    On success returns a dict::

        {
            "state": "success",
            "agent": <full agent response dict>,
            "message": "upgrade completed successfully"
        }

    On failure raises ``RuntimeError`` with the terminal error message.
    On timeout raises ``TimeoutError``.

    :param blueprint_id: Blueprint UUID (used for last-job-log on error).
    :param agent_id:     Global system-agent UUID.
    :param timeout:      Maximum seconds to wait.
    """
    deadline = time.time() + timeout

    # Allow a brief startup delay so the job appears in last_job_status
    time.sleep(5)

    while time.time() < deadline:
        agent = get_global_agent(client_factory, agent_id)
        if agent is None:
            raise ValueError(f"Agent '{agent_id}' no longer exists during upgrade poll")

        last_job = agent.get("last_job_status", {})
        state = last_job.get("state", "")

        if state == "success":
            return {
                "state": "success",
                "agent": agent,
                "message": "upgrade completed successfully",
            }

        if state in {"error", "failed"}:
            # Try to fetch the detailed job log
            log_text = _get_last_job_log(client_factory, blueprint_id, agent_id)
            err_msg = last_job.get("message") or log_text or state
            raise RuntimeError(f"Upgrade job for agent '{agent_id}' failed: {err_msg}")

        # Not yet terminal — wait and re-poll
        remaining = deadline - time.time()
        sleep_time = min(_DEFAULT_POLL_INTERVAL, max(0, remaining))
        time.sleep(sleep_time)

    raise TimeoutError(
        f"Upgrade job for agent '{agent_id}' did not complete within {timeout}s"
    )


def _get_last_job_log(client_factory, blueprint_id, agent_id):
    """Attempt to fetch the last-job log text; return empty string on failure.

    Uses the global ``/system-agents/{id}/last-job-log`` endpoint.
    The *blueprint_id* parameter is kept for interface compatibility.
    """
    try:
        base = client_factory.get_base_client()
        return base.system_agents[agent_id].last_job_log()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Upgrade-group membership helpers (used by upgrade_group module)
# ---------------------------------------------------------------------------


def list_all_systems(client_factory):
    """Return all items from ``GET /api/systems`` (global).

    Each item includes ``device_key``, ``facts``, ``status``,
    and ``user_config`` (which holds ``upgrade_group``).
    """
    base = client_factory.get_base_client()
    resp = base.raw_request("/systems")
    if resp.status_code != 200:
        raise Exception(f"GET /systems failed: {resp.status_code} {resp.text}")
    data = resp.json()
    return data.get("items", []), data.get("upgrade_groups", [])


def resolve_device_key(client_factory, system_ref, blueprint_id=None):
    """Resolve *system_ref* to a ``device_key`` for ``PUT /systems/{key}``.

    Resolution order (first match wins):

    1. Direct ``device_key`` match (MAC/serial, e.g. ``525400D8C496``).
    2. Management-IP match against ``facts.mgmt_ipaddr``.
    3. Hostname match against ``facts.hostname`` (often ``None`` on cloud
       Apstra installs).
    4. Blueprint-node label via
       ``/blueprints/{bp}/experience/web/system-info``
       (requires *blueprint_id*; resolves human-readable node labels like
       ``apstra_esi_001_leaf1`` — the ``system_id`` returned by that
       endpoint is identical to ``device_key`` in ``/systems``).

    Raises ``ValueError`` if not found.
    """
    items, _groups = list_all_systems(client_factory)

    # Steps 1–3: direct match in /systems
    for system in items:
        device_key = system.get("device_key", "")
        facts = system.get("facts", {})
        hostname = facts.get("hostname", "") or ""
        mgmt_ip = facts.get("mgmt_ipaddr", "") or ""
        if (
            device_key == system_ref
            or mgmt_ip == system_ref
            or (hostname and hostname == system_ref)
        ):
            return device_key

    # Step 4: blueprint-node label → system_id (== device_key)
    if blueprint_id:
        sys_info = list_blueprint_system_info(client_factory, blueprint_id)
        for node in sys_info:
            if node.get("label") == system_ref and node.get("system_id"):
                node_sys_id = node["system_id"]
                # system_id == device_key in /systems
                for system in items:
                    if system.get("device_key") == node_sys_id:
                        return node_sys_id
    raise ValueError(
        f"System not found for '{system_ref}'. "
        "Provide a device_key, management IP, hostname, or blueprint node label."
    )


def get_group_members(client_factory, group_name):
    """Return a list of systems that currently belong to *group_name*.

    Each entry is the full system dict from ``GET /systems`` (contains
    ``device_key``, ``facts``, ``user_config``, etc.).
    Returns an empty list when the group does not exist.
    """
    items, _groups = list_all_systems(client_factory)
    return [
        s for s in items if s.get("user_config", {}).get("upgrade_group") == group_name
    ]


def set_upgrade_group(client_factory, device_key, group_name, current_user_config=None):
    """PUT ``/api/systems/{device_key}`` to set ``user_config.upgrade_group``.

    Preserves all existing ``user_config`` fields (including required fields
    like ``aos_hcl_model`` and ``admin_state``).
    Returns ``True`` if changed, ``False`` if already in the target group.

    NOTE: The individual GET ``/systems/{key}`` endpoint in Apstra 6.1 may
    return an incomplete ``user_config`` (e.g. empty ``aos_hcl_model``) while
    the list GET ``/systems`` returns the full record.  Always pass the
    ``current_user_config`` obtained from the list to avoid this.
    """
    base = client_factory.get_base_client()

    # If not supplied, fetch via the individual endpoint and patch any
    # empty required fields from facts (last resort — list endpoint preferred).
    if current_user_config is None:
        resp = base.raw_request(f"/systems/{device_key}")
        if resp.status_code != 200:
            raise Exception(
                f"GET /systems/{device_key} failed: {resp.status_code} {resp.text}"
            )
        data = resp.json()
        current_user_config = dict(data.get("user_config", {}))
        # Individual endpoint may return empty aos_hcl_model — fall back to facts
        if not current_user_config.get("aos_hcl_model"):
            facts = data.get("facts", {})
            model = (
                facts.get("aos_hcl_model")
                or facts.get("hcl_model")
                or facts.get("os_family")
                or ""
            )
            current_user_config["aos_hcl_model"] = model

    if current_user_config.get("upgrade_group") == group_name:
        return False  # Already in target group — idempotent

    # Build the PUT body from the list-sourced user_config (which is complete).
    new_user_config = dict(current_user_config)
    new_user_config["upgrade_group"] = group_name

    put_body = {"user_config": new_user_config}
    resp = base.raw_request(f"/systems/{device_key}", "PUT", data=put_body)
    if resp.status_code not in (200, 201, 204):
        raise Exception(
            f"PUT /systems/{device_key} failed: {resp.status_code} {resp.text}\n"
            f"  user_config sent: {new_user_config}"
        )
    return True  # Changed
