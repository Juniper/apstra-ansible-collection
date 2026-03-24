# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint EVPN Interconnect Domain utilities.

Provides reusable helpers for managing EVPN Interconnect Domains
(``evpn_interconnect_group`` in the Apstra API) within a blueprint via
``raw_request`` — the SDK does not expose these endpoints.

API endpoints::

    POST   /api/blueprints/{bp_id}/evpn-interconnect-groups           → create
    GET    /api/blueprints/{bp_id}/evpn-interconnect-groups           → list all
    GET    /api/blueprints/{bp_id}/evpn-interconnect-groups/{id}      → get one
    PUT    /api/blueprints/{bp_id}/evpn-interconnect-groups/{id}      → update
    DELETE /api/blueprints/{bp_id}/evpn-interconnect-groups/{id}      → delete

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interconnect_domain import (
        list_interconnect_domains,
        get_interconnect_domain,
        create_interconnect_domain,
        update_interconnect_domain,
        delete_interconnect_domain,
        find_interconnect_domain_by_label,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

_BASE_PATH = "/blueprints/{bp_id}/evpn-interconnect-groups"


# ──────────────────────────────────────────────────────────────────
#  Collection operations
# ──────────────────────────────────────────────────────────────────


def list_interconnect_domains(client_factory, blueprint_id):
    """List all EVPN Interconnect Domains in a blueprint.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        list[dict]: List of interconnect domain dicts.  Returns an
        empty list when none exist.
    """
    base = client_factory.get_base_client()
    url = _BASE_PATH.format(bp_id=blueprint_id)
    resp = base.raw_request(url)
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("items", [])
    return []


def find_interconnect_domain_by_label(client_factory, blueprint_id, label):
    """Find an interconnect domain by its label.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        label: The label to search for.

    Returns:
        dict or None: The matching domain dict, or *None*.
    """
    domains = list_interconnect_domains(client_factory, blueprint_id)
    for domain in domains:
        if domain.get("label") == label:
            return domain
    return None


# ──────────────────────────────────────────────────────────────────
#  Single-object operations
# ──────────────────────────────────────────────────────────────────


def get_interconnect_domain(client_factory, blueprint_id, domain_id):
    """Get a specific EVPN Interconnect Domain.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        domain_id: The interconnect domain UUID.

    Returns:
        dict or None: The domain dict, or *None* if not found.
    """
    base = client_factory.get_base_client()
    url = _BASE_PATH.format(bp_id=blueprint_id) + f"/{domain_id}"
    resp = base.raw_request(url)
    if resp.status_code == 200:
        return resp.json()
    return None


def create_interconnect_domain(client_factory, blueprint_id, data):
    """Create an EVPN Interconnect Domain.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        data: The create payload (dict).

    Returns:
        dict: The API response (typically contains ``id``).

    Raises:
        Exception: If the POST request fails.
    """
    base = client_factory.get_base_client()
    url = _BASE_PATH.format(bp_id=blueprint_id)
    resp = base.raw_request(url, "POST", data=data)
    if resp.status_code not in (200, 201, 202):
        raise Exception(
            f"POST evpn-interconnect-groups failed: " f"{resp.status_code} {resp.text}"
        )
    return resp.json()


def update_interconnect_domain(client_factory, blueprint_id, domain_id, data):
    """Update an EVPN Interconnect Domain (PUT — full replace).

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        domain_id: The interconnect domain UUID.
        data: The update payload (dict).

    Returns:
        dict or None: The API response, or *None* on 204.

    Raises:
        Exception: If the PUT request fails.
    """
    base = client_factory.get_base_client()
    url = _BASE_PATH.format(bp_id=blueprint_id) + f"/{domain_id}"
    resp = base.raw_request(url, "PUT", data=data)
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"PUT evpn-interconnect-groups failed: " f"{resp.status_code} {resp.text}"
        )
    if resp.status_code == 204 or not resp.text:
        return None
    return resp.json()


def delete_interconnect_domain(client_factory, blueprint_id, domain_id):
    """Delete an EVPN Interconnect Domain.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        domain_id: The interconnect domain UUID.

    Raises:
        Exception: If the DELETE request fails.
    """
    base = client_factory.get_base_client()
    url = _BASE_PATH.format(bp_id=blueprint_id) + f"/{domain_id}"
    resp = base.raw_request(url, "DELETE")
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"DELETE evpn-interconnect-groups failed: "
            f"{resp.status_code} {resp.text}"
        )
