.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.allowed_list_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.allowed_list module -- Manage platform-level IP/subnet allow list in Apstra
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.2.0).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.allowed_list`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 1.2.0

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- Manage platform-level IP/subnet allow list (white-list) in Apstra.
- Trusted IP/subnets are never locked out, even if they violate rate limit rules.
- Maps to C(/api/aaa/ratelimit/allowlist).
- Supports IP/subnet add (create), edit (update), delete, and query (list) operations.
- Changes to the allowed list are recorded in the event log.


Parameters
----------

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Parameter
    - Type
    - Required
    - Description

  * - api_url
    - string
    - false
    - Apstra API URL. Defaults to C(APSTRA_API_URL) env var.

  * - verify_certificates
    - boolean
    - false
    - Verify TLS certificates. Default: C(true)

  * - username
    - string
    - false
    - Apstra username for SDK login. Defaults to C(APSTRA_USERNAME) env var.

  * - password
    - string
    - false
    - Apstra password for SDK login. Defaults to C(APSTRA_PASSWORD) env var.

  * - auth_token
    - string
    - false
    - Pre-existing auth token. Defaults to C(APSTRA_AUTH_TOKEN) env var.

  * - ip_subnet
    - string
    - false
    - | IP address or subnet CIDR notation to add/remove from the allow list.
      | Required for C(state) C(present) or C(absent).
      | Examples: C(192.168.1.10), C(10.0.0.0/24), C(2001:db8::1/32).

  * - comment
    - string
    - false
    - | Optional comment/description for the IP/subnet.
      | Applicable when C(state) is C(present).

  * - state
    - string
    - false
    - | Desired state of the allow list entry.
      | C(present) - add or update an IP/subnet (default).
      | C(absent) - remove an IP/subnet.
      | C(query) - retrieve all entries in the allow list.


Examples
--------

.. code-block:: yaml+jinja

  - name: Add IP address to allowed list with comment
    juniper.apstra.allowed_list:
      ip_subnet: "192.168.1.100"
      comment: "Management workstation"
      state: present

  - name: Add subnet to allowed list
    juniper.apstra.allowed_list:
      ip_subnet: "10.0.0.0/8"
      comment: "Corporate network"
      state: present

  - name: Update comment for existing allowed entry
    juniper.apstra.allowed_list:
      ip_subnet: "192.168.1.100"
      comment: "Updated management workstation"
      state: present

  - name: Remove IP from allowed list
    juniper.apstra.allowed_list:
      ip_subnet: "192.168.1.100"
      state: absent

  - name: Query all allowed IPs/subnets
    juniper.apstra.allowed_list:
      state: query
    register: result

  - name: Show all allowed entries
    debug:
      msg: "{{ result.allowed_list }}"


Return Values
-------------

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Key
    - Type
    - Returned
    - Description

  * - changed
    - boolean
    - always
    - Whether any change was made.

  * - message
    - string
    - always
    - Result message.

  * - allowed_list
    - list
    - when state is C(query)
    - | List of all IP/subnet entries in the allowed list.
      | Each item typically includes C(subnet) and may include C(comment).

  * - entry
    - dict
    - when state is C(present) and change is made
    - | The created or updated allow list entry.
      | Depending on SDK response, this may include C(id), C(subnet), and C(comment).

  * - id
    - string
    - when entry exists
    - | The ID of the entry.


Status
------

- This module is not guaranteed to have a backwards compatible interface.


Authors
-------

- Shirish Ranoji (@sranoji)
