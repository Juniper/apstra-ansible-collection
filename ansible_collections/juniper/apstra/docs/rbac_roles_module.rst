.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.rbac_roles_module:

.. Title

juniper.apstra.rbac_roles module -- Manage platform RBAC roles in Apstra
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.0.5).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.rbac_roles`.

.. rst-class:: ansible-version-added

New in juniper.apstra 1.1.0

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- Manage platform (controller-level) RBAC roles in Apstra.
- Maps to ``/api/aaa/roles``.
- Supports role create, update, delete, and idempotent checks.
- ``body.type`` is required for ``state: present`` and must be ``global`` or ``granular``.
- ``granular_permissions[].scope`` accepts only shorthand blueprint IDs (string or list), which the module expands to ``blueprint_id in [...]``.

Parameters
----------

- ``api_url`` (str): Apstra API URL. Default: ``APSTRA_API_URL`` environment variable.
- ``verify_certificates`` (bool): Verify TLS certificates. Default: ``true``.
- ``username`` (str): Apstra username. Default: ``APSTRA_USERNAME`` environment variable.
- ``password`` (str): Apstra password. Default: ``APSTRA_PASSWORD`` environment variable.
- ``auth_token`` (str): Pre-existing auth token. Default: ``APSTRA_AUTH_TOKEN`` environment variable.
- ``id`` (dict): Optional role id dictionary. ``id.role`` can be role UUID or role name.
- ``body`` (dict): Role definition.

  - Required for ``state: present``.
  - Role identifier via ``body.role`` (or ``body.name`` alias).
  - ``body.type`` required for ``state: present`` with values ``global`` or ``granular``.
  - ``granular_permissions`` / ``blueprint_permissions`` scopes must be shorthand blueprint IDs (full scope expressions are rejected).

- ``state`` (str): Desired state. Choices: ``present`` (default), ``absent``.

Examples
--------

.. code-block:: yaml

  - name: Create global role
    juniper.apstra.rbac_roles:
      body:
        role: custom_role_ansible
        type: global
        label: custom_role_ansible
        description: Custom role from ansible
        permissions:
          - core.blueprints.read
      state: present

  - name: Create granular role for selected blueprints
    juniper.apstra.rbac_roles:
      body:
        role: bp_reader
        type: granular
        granular_permissions:
          - scope:
              - blueprint-id-1
              - blueprint-id-2
            permissions:
              - rbac.blueprint.read
      state: present

  - name: Delete role
    juniper.apstra.rbac_roles:
      body:
        role: custom_role_ansible
      state: absent

Return Values
-------------

- ``changed`` (bool): Whether any change was made.
- ``id`` (dict): Resolved role id dictionary.
- ``role`` (dict): Full role object when ``state`` is ``present``.
- ``changes`` (dict): Fields changed during update.
- ``msg`` (str): Result message.
