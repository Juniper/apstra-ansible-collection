# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""DCI (Data Center Interconnect) blueprint utilities.

Provides reusable helpers for DCI-specific operations that previously
required direct REST API calls via the ``uri`` module:

* Blueprint build-error checking
* PATCH of interconnect domains with L3/VN fields the SDK does not
  expose (``enabled_for_l3``, ``l3_interconnect_route_target``,
  ``interconnect_security_zones``, ``interconnect_virtual_networks``)

Usage inside a module or test helper::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_dci import (
        get_blueprint_errors,
        patch_interconnect_domain_raw,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# ──────────────────────────────────────────────────────────────────
#  Build error helpers
# ──────────────────────────────────────────────────────────────────


def get_blueprint_errors(client_factory, blueprint_id):
    """Retrieve build errors for a blueprint.

    Calls ``GET /api/blueprints/{bp_id}/errors`` via ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        dict: The errors payload.  Typically contains
        ``errors_count``, ``warnings_count`` and per-category dicts
        (``nodes``, ``relationships``).  Returns an empty dict on
        failure.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/errors")
    if resp.status_code == 200:
        return resp.json()
    return {}


def has_build_errors(client_factory, blueprint_id):
    """Return *True* if the blueprint has unresolved build errors.

    Ignores ``version``, ``errors_count``, and ``warnings_count``
    metadata keys — only checks for non-empty error dicts.
    """
    errors = get_blueprint_errors(client_factory, blueprint_id)
    ignore_keys = {"version", "errors_count", "warnings_count"}
    for key, value in errors.items():
        if key in ignore_keys:
            continue
        if value:  # non-empty dict / list
            return True
    return False


# ──────────────────────────────────────────────────────────────────
#  Raw PATCH for interconnect domain (L3 + VN fields)
# ──────────────────────────────────────────────────────────────────


def patch_interconnect_domain_raw(client_factory, blueprint_id, domain_id, patch_data):
    """PATCH an EVPN Interconnect Domain with arbitrary fields.

    The AOS SDK's ``evpn_interconnect_groups`` resource only exposes
    ``label``, ``interconnect_route_target``, and
    ``interconnect_esi_mac`` as keyword arguments on ``create()`` /
    ``update()``.  Fields such as ``enabled_for_l3``,
    ``l3_interconnect_route_target``, ``interconnect_security_zones``,
    and ``interconnect_virtual_networks`` must be sent via raw REST.

    Calls::

        PATCH /api/blueprints/{bp_id}/evpn_interconnect_groups/{domain_id}

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        domain_id: The ``evpn_interconnect_group`` UUID.
        patch_data: A dict of fields to patch.  Example::

            {
                "interconnect_security_zones": {
                    "<sz_node_id>": {
                        "routing_policy_id": "<rp_node_id>",
                        "interconnect_route_target": "65500:200",
                        "enabled_for_l3": True,
                    }
                }
            }

    Returns:
        dict or None: The API response body, or *None* on 204.

    Raises:
        Exception: If the PATCH fails.
    """
    base = client_factory.get_base_client()
    path = f"/blueprints/{blueprint_id}" f"/evpn_interconnect_groups/{domain_id}"
    resp = base.raw_request(path, "PATCH", data=patch_data)
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to PATCH interconnect domain {domain_id}: "
            f"{resp.status_code} {resp.text}"
        )
    try:
        return resp.json()
    except Exception:
        return None
