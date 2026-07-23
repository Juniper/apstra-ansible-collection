.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.rbac_user_module:

.. Title

juniper.apstra.rbac_user module -- Manage platform RBAC users in Apstra
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.0.5).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.rbac_user`.

.. rst-class:: ansible-version-added

New in juniper.apstra 1.1.0

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- Manage platform (controller-level) users in Apstra.
- Maps to ``/api/aaa/users`` and ``/api/aaa/users/{id}/roles``.
- Users are identified by ``username``; the module resolves UUID automatically.
- Supports create, update profile fields, role assignments, password rotation, and delete.

Parameters
----------

- ``api_url`` (str): Apstra API URL. Default: ``APSTRA_API_URL`` environment variable.
- ``verify_certificates`` (bool): Verify TLS certificates. Default: ``true``.
- ``username`` (str): Apstra username. Default: ``APSTRA_USERNAME`` environment variable.
- ``password`` (str): Apstra password. Default: ``APSTRA_PASSWORD`` environment variable.
- ``auth_token`` (str): Pre-existing auth token. Default: ``APSTRA_AUTH_TOKEN`` environment variable.
- ``id`` (dict): Optional id dictionary (usually omitted). ``id.user`` may be used.
- ``body`` (dict): User definition.

  - Required identifier: ``body.username``.
  - Create requires ``body.password``.
  - Optional profile fields: ``first_name``, ``last_name``, ``email``.
  - Role management via ``roles`` list.
  - Password rotation via ``change_password.old`` and ``change_password.new``.

- ``state`` (str): Desired state. Choices: ``present`` (default), ``absent``.

Examples
--------

.. code-block:: yaml

  - name: Create alice with viewer role
    juniper.apstra.rbac_user:
      body:
        username: alice
        password: "S3cret!Pass"
        first_name: Alice
        last_name: Liddell
        email: alice@example.com
        roles: [viewer]
      state: present

  - name: Update alice profile
    juniper.apstra.rbac_user:
      body:
        username: alice
        first_name: "Alice (mgr)"
      state: present

  - name: Rotate alice password
    juniper.apstra.rbac_user:
      body:
        username: alice
        change_password:
          old: "S3cret!Pass"
          new: "S3cret!Pass2"
      state: present

  - name: Delete alice
    juniper.apstra.rbac_user:
      body:
        username: alice
      state: absent

Return Values
-------------

- ``changed`` (bool): Whether any change was made.
- ``id`` (dict): Resolved user id dictionary.
- ``user`` (dict): Full user object when ``state`` is ``present``.
- ``changes`` (dict): Fields changed during update.
- ``msg`` (str): Result message.
