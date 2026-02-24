# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""
Connectivity Template — Validation
====================================

Validates that the primitives supplied by the user are legal for the
chosen CT ``type`` and that nesting (child primitives) follows the
rules defined in :mod:`ct_primitives`.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ct_primitives import (
    PRIMITIVE_TYPES,
    PLURAL_TO_SINGULAR,
    ALLOWED_PRIMITIVES,
    CHILD_PRIMITIVES,
)


class CTValidationError(Exception):
    """Raised when CT validation fails."""


def validate_primitives(ct_type, primitives):
    """
    Validate a user-supplied *primitives* dict against the rules for
    *ct_type*.

    Parameters
    ----------
    ct_type : str
        One of ``interface``, ``svi``, ``loopback``,
        ``protocol_endpoint``, ``system``.
    primitives : dict
        Dict-of-dicts keyed by **plural** primitive type name. E.g.::

            {
                "ip_links": {
                    "link1": {
                        "routing_zone_id": "...",
                        "bgp_peering_generic_systems": {
                            "peer1": { ... }
                        }
                    }
                }
            }

    Raises
    ------
    CTValidationError
        If any validation rule is violated.
    """
    if not isinstance(primitives, dict):
        raise CTValidationError(
            "primitives must be a dict keyed by plural primitive type name"
        )

    allowed = ALLOWED_PRIMITIVES.get(ct_type, [])

    for plural_key, instances in primitives.items():
        singular = PLURAL_TO_SINGULAR.get(plural_key)
        if singular is None:
            valid_keys = ", ".join(sorted(PLURAL_TO_SINGULAR.keys()))
            raise CTValidationError(
                f"Unknown primitive type key '{plural_key}'. "
                f"Valid keys: {valid_keys}"
            )

        if singular not in allowed:
            allowed_plural = ", ".join(
                sorted(k for k, v in PLURAL_TO_SINGULAR.items() if v in allowed)
            )
            raise CTValidationError(
                f"Primitive '{plural_key}' is not allowed for CT type "
                f"'{ct_type}'. Allowed top-level primitives: "
                f"{allowed_plural}"
            )

        if not isinstance(instances, dict):
            raise CTValidationError(
                f"primitives.{plural_key} must be a dict of named "
                f"instances, got {type(instances).__name__}"
            )

        for inst_name, inst_config in instances.items():
            if not isinstance(inst_config, dict):
                raise CTValidationError(
                    f"primitives.{plural_key}.{inst_name} must be a "
                    f"dict, got {type(inst_config).__name__}"
                )
            _validate_children(
                singular, inst_config, f"primitives.{plural_key}.{inst_name}"
            )


def _validate_children(parent_type, config, path):
    """
    Recursively validate child primitives nested inside *config* for
    a primitive of *parent_type*.
    """
    allowed_children = CHILD_PRIMITIVES.get(parent_type, [])

    for key, value in config.items():
        child_singular = PLURAL_TO_SINGULAR.get(key)
        if child_singular is None:
            # Not a primitive type key — it's an attribute, skip
            continue

        # It is a primitive key — validate nesting
        if child_singular not in allowed_children:
            allowed_keys = (
                ", ".join(
                    sorted(
                        k
                        for k, v in PLURAL_TO_SINGULAR.items()
                        if v in allowed_children
                    )
                )
                or "(none)"
            )
            raise CTValidationError(
                f"{path}: child primitive '{key}' is not allowed "
                f"inside '{parent_type}'. Allowed children: "
                f"{allowed_keys}"
            )

        if not isinstance(value, dict):
            raise CTValidationError(
                f"{path}.{key} must be a dict of named instances, "
                f"got {type(value).__name__}"
            )

        for child_name, child_config in value.items():
            if not isinstance(child_config, dict):
                raise CTValidationError(
                    f"{path}.{key}.{child_name} must be a dict, "
                    f"got {type(child_config).__name__}"
                )
            _validate_children(
                child_singular, child_config, f"{path}.{key}.{child_name}"
            )
