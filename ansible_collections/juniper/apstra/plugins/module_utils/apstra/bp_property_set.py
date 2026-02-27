# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint property-set utilities.

Provides helpers for blueprint-scoped property-set operations that
the AOS SDK does not expose natively.

The SDK ``freeform_client`` covers:
  - ``blueprints[bp_id].property_sets[ps_id].get()``   → GET
  - ``blueprints[bp_id].property_sets[ps_id].patch()``  → PATCH
  - ``blueprints[bp_id].property_sets[ps_id].delete()`` → DELETE

But it does **not** have ``.update()`` (PUT), which is required to
reimport a global property set into a blueprint when the global
values have changed.

This module fills that gap using ``raw_request``.

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_property_set import (
        reimport_blueprint_property_set,
    )

    reimport_blueprint_property_set(
        client_factory, blueprint_id, property_set_id, body
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


def reimport_blueprint_property_set(
    client_factory, blueprint_id, property_set_id, body
):
    """Reimport (PUT) a property set into a blueprint.

    Calls ``PUT /api/blueprints/{bp_id}/property-sets/{ps_id}`` via
    ``raw_request`` because the SDK freeform client has no
    ``.update()`` on blueprint property-set resources.

    Compares the blueprint property-set values before and after the
    PUT to determine whether the reimport changed anything.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        property_set_id: The property-set UUID (global PS id used
            as the key inside the blueprint).
        body: The PUT payload, typically ``{"id": "<global_ps_id>"}``.

    Returns:
        dict: ``{"changed": bool, "msg": str}`` indicating whether
        the reimport updated the blueprint copy.

    Raises:
        Exception: If the PUT request returns a non-success status.
    """
    id_for_get = {
        "blueprint": blueprint_id,
        "property_set": property_set_id,
    }

    # Snapshot values before reimport
    before = client_factory.object_request(
        "blueprints.property_sets", "get", id_for_get
    )
    before_values = before.get("values") if before else None

    # PUT /api/blueprints/{bp_id}/property-sets/{ps_id}
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/property-sets/{property_set_id}",
        method="PUT",
        data=body,
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"PUT property-sets reimport failed: " f"{resp.status_code} {resp.text}"
        )

    # Snapshot values after reimport
    after = client_factory.object_request("blueprints.property_sets", "get", id_for_get)
    after_values = after.get("values") if after else None

    return {
        "changed": before_values != after_values,
        "msg": (
            "property_set reimported successfully"
            if before_values != after_values
            else "property_set reimported (values unchanged)"
        ),
    }
