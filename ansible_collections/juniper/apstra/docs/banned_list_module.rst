.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.banned_list_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.banned_list module -- Manage platform-level IP/subnet ban list (denylist) in Apstra
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.2.0).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.banned_list`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 1.2.0

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- Manage platform-level IP/subnet ban list (denylist) in Apstra.
- IP/subnets that violate rate limit rules are automatically added to the banned list and are locked out for the configured lockout period.
- Admins can remove IP/subnets from the banned list to immediately allow logins from that IP/subnet.
- Maps to C(/api/aaa/ratelimit/denylist).
- Supports IP/subnet delete and query operations only (entries are auto-added by the rate limiter).
- Changes to the banned list are recorded in the event log.


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
    - | IP address or subnet CIDR notation to remove from the ban list.
      | Required for C(state) C(absent).
      | Note - entries cannot be manually created; they are automatically added
      |   by the rate limiter when IP/subnets violate rate limit rules.
      | Examples: C(192.168.1.10), C(10.0.0.0/24), C(2001:db8::1/32).

  * - state
    - string
    - false
    - | Desired state for ban list management.
      | C(absent) - remove an IP/subnet from the ban list.
      | C(query) - retrieve all entries in the ban list (default).
      | Note - C(present) is not supported since entries are auto-added.


Examples
--------

.. code-block:: yaml+jinja

  - name: List all banned IP addresses
    juniper.apstra.banned_list:
      state: query
    register: result

  - name: Show all banned entries
    debug:
      msg: "{{ result.banned_list }}"

  - name: Remove IP from ban list (allow it to login again)
    juniper.apstra.banned_list:
      ip_subnet: "192.168.1.100"
      state: absent

  - name: Unban a subnet
    juniper.apstra.banned_list:
      ip_subnet: "10.0.0.0/24"
      state: absent


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

  * - banned_list
    - list
    - when state is C(query)
    - | List of all IP/subnet entries in the ban list (denylist).
      | Each item typically includes C(subnet).

  * - id
    - string
    - when entry is removed
    - | The ID of the entry removed (if applicable).


Status
------

- This module is not guaranteed to have a backwards compatible interface.


Authors
-------

- Shirish Ranoji (@sranoji)
