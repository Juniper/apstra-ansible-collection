.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.blueprint_health_module:

.. Title

juniper.apstra.blueprint_health module -- Collect anomalies and build errors from an Apstra blueprint
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_.

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.blueprint_health`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 1.0.9

.. contents::
   :local:
   :depth: 1


Synopsis
--------

.. Description

- This module collects anomalies and build errors/warnings from an Apstra blueprint as structured data for monitoring, alerting, and reporting.
- Anomalies are retrieved via ``GET /api/blueprints/{id}/anomalies``.
- Build errors are retrieved via ``GET /api/blueprints/{id}/errors``.
- Results can be filtered by scope, severity, anomaly type, and node.


Parameters
----------

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Parameter
    - Comments

  * - **api_url** (string)
    - The URL used to access the Apstra API.

  * - **auth_token** (string)
    - The authentication token to use if already authenticated.

  * - **id** (dictionary, **required**)
    - Dictionary containing the blueprint identifier. Must include a ``blueprint`` key with the blueprint ID or label.

  * - **scope** (string)
    - The type of health data to collect. Choices: ``anomalies``, ``errors``, ``all``. Default: ``all``.

  * - **severity** (string)
    - Filter results by severity level. Choices: ``critical``, ``warning``, ``info``.

  * - **node_filter** (string)
    - Filter anomalies by system/node name or ID.

  * - **anomaly_type** (string)
    - Filter anomalies by anomaly type (e.g. ``cabling``, ``config``, ``bgp``, ``route``).

  * - **username** (string)
    - The username for authentication.

  * - **password** (string)
    - The password for authentication.

  * - **verify_certificates** (boolean)
    - If set to false, SSL certificates will not be verified. Default: ``true``.


Return Values
-------------

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Key
    - Description

  * - **changed** (boolean)
    - Always false since this is a read-only module.

  * - **anomalies** (dictionary)
    - Anomaly data from the blueprint. Returned when scope is ``anomalies`` or ``all``.

  * - **errors** (dictionary)
    - Build errors and warnings from the blueprint. Returned when scope is ``errors`` or ``all``.

  * - **msg** (string)
    - Summary message with anomaly and error counts.


Examples
--------

.. code-block:: yaml

    - name: Collect all health data from a blueprint
      juniper.apstra.blueprint_health:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      register: health

    - name: Collect anomalies only
      juniper.apstra.blueprint_health:
        id:
          blueprint: "my-blueprint-label"
        scope: anomalies

    - name: Collect only critical anomalies
      juniper.apstra.blueprint_health:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        scope: anomalies
        severity: critical

    - name: Collect build errors only
      juniper.apstra.blueprint_health:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        scope: errors


Authors
-------

- Prabhanjan KV (@kvp_jnpr)
