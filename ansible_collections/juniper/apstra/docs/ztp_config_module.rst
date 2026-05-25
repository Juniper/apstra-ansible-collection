.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.ztp_config_module:

.. Title

juniper.apstra.ztp_config module -- Manage ZTP VM configuration
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_.

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.ztp_config`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 0.1.0

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- This module manages the Apstra ZTP VM configuration including DHCP host-reservations, subnets, pools, firmware mappings, and passwords.
- The ZTP VM is a separate appliance from the Apstra server and requires its own connection parameters (``ztp_url``, ``ztp_username``, ``ztp_password``).
- Three configuration scopes are supported via the ``scope`` parameter: ``dhcp_configurator``, ``ztp_config``, and ``password``.
- The module is idempotent — it reads the current configuration, compares it with the desired state, and only applies changes when differences exist.

Parameters
----------

.. raw:: html

  <table  border=0 cellpadding=0 class="documentation-table">
      <tr>
          <th>Parameter</th>
          <th>Choices/<font color="blue">Defaults</font></th>
          <th>Description</th>
      </tr>
      <tr>
          <td><b>ztp_url</b> (string)</td>
          <td></td>
          <td>Base URL of the ZTP VM (e.g., <code>https://10.204.22.128</code>). Can also be set via the <code>ZTP_URL</code> environment variable.</td>
      </tr>
      <tr>
          <td><b>ztp_username</b> (string)</td>
          <td></td>
          <td>Username for ZTP VM authentication. Can also be set via the <code>ZTP_USERNAME</code> environment variable.</td>
      </tr>
      <tr>
          <td><b>ztp_password</b> (string)</td>
          <td></td>
          <td>Password for ZTP VM authentication. Can also be set via the <code>ZTP_PASSWORD</code> environment variable.</td>
      </tr>
      <tr>
          <td><b>ztp_auth_token</b> (string)</td>
          <td></td>
          <td>Pre-existing auth token for the ZTP VM. Can also be set via the <code>ZTP_AUTH_TOKEN</code> environment variable.</td>
      </tr>
      <tr>
          <td><b>ztp_verify_certificates</b> (boolean)</td>
          <td><font color="blue">false</font></td>
          <td>Whether to verify SSL certificates when connecting to the ZTP VM.</td>
      </tr>
      <tr>
          <td><b>scope</b> (string) / <em>required</em></td>
          <td><ul><li>dhcp_configurator</li><li>ztp_config</li><li>password</li></ul></td>
          <td>The configuration scope to manage. <code>dhcp_configurator</code> manages DHCP subnets, pools, host-reservations, and DHCP options. <code>ztp_config</code> manages firmware mappings, default passwords, and ZTP workflow settings. <code>password</code> changes the ZTP web UI admin password.</td>
      </tr>
      <tr>
          <td><b>state</b> (string)</td>
          <td><ul><li><font color="blue"><b>present</b></font></li><li>absent</li><li>query</li></ul></td>
          <td>Desired state. <code>present</code> creates or updates configuration. <code>absent</code> removes specific items (dhcp_configurator only). <code>query</code> retrieves the current configuration.</td>
      </tr>
      <tr>
          <td><b>subnets</b> (list)</td>
          <td></td>
          <td>List of subnet definitions for DHCP. Each subnet includes <code>subnet</code> (CIDR), <code>router</code> (gateway IP), <code>pools</code> (IP ranges), and optional <code>host-reservations</code>.</td>
      </tr>
      <tr>
          <td><b>host_reservations</b> (list)</td>
          <td></td>
          <td>List of MAC-to-IP host reservations. Each entry: <code>hw-address</code>, <code>ip-address</code>, optional <code>hostname</code>.</td>
      </tr>
      <tr>
          <td><b>global_host_reservations</b> (list)</td>
          <td></td>
          <td>List of global (outside-subnet) host reservations. Same format as <code>host_reservations</code>.</td>
      </tr>
      <tr>
          <td><b>options</b> (dict)</td>
          <td></td>
          <td>DHCP options: <code>domain-name</code>, <code>domain-search</code>, <code>domain-name-servers</code> (list), <code>tftp-server-name</code>.</td>
      </tr>
      <tr>
          <td><b>reservation_mode_default</b> (list)</td>
          <td></td>
          <td>Default DHCP reservation mode: <code>all</code>, <code>global</code>, <code>out-of-pool</code>, <code>disabled</code>.</td>
      </tr>
      <tr>
          <td><b>firmware</b> (dict)</td>
          <td></td>
          <td>ZTP JSON configuration keyed by platform (<code>defaults</code>, <code>junos</code>, <code>nxos</code>, <code>eos</code>, <code>junos-evo</code>). Used with <code>scope=ztp_config</code>.</td>
      </tr>
      <tr>
          <td><b>old_password</b> (string)</td>
          <td></td>
          <td>Current ZTP admin password. Required for <code>scope=password</code>.</td>
      </tr>
      <tr>
          <td><b>new_password</b> (string)</td>
          <td></td>
          <td>New ZTP admin password. Required for <code>scope=password</code>.</td>
      </tr>
  </table>

Notes
-----

.. note::
   - The ZTP VM is a separate appliance from the Apstra server. Connection parameters (``ztp_url``, ``ztp_username``, ``ztp_password``) are distinct from Apstra server parameters.
   - Environment variables ``ZTP_URL``, ``ZTP_USERNAME``, ``ZTP_PASSWORD``, ``ZTP_AUTH_TOKEN``, and ``ZTP_VERIFY_CERTIFICATES`` can be used instead of module parameters.
   - DHCP configuration changes via the configurator endpoint automatically restart the DHCP service.
   - The ``state=absent`` option is only supported for ``scope=dhcp_configurator`` (to remove host-reservations or subnets).

Examples
--------

.. code-block:: yaml+jinja

    # Query current DHCP configuration
    - name: Get DHCP config
      juniper.apstra.ztp_config:
        ztp_url: "https://192.168.50.2"
        ztp_username: "admin"
        ztp_password: "Apstramarvis@123"
        ztp_verify_certificates: false
        scope: dhcp_configurator
        state: query
      register: dhcp_config

    # Configure DHCP subnets with host reservations
    - name: Configure DHCP
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: present
        options:
          domain-name: "ztplab.local"
          domain-name-servers:
            - "8.8.8.8"
            - "8.8.4.4"
          tftp-server-name: "192.168.50.2"
        subnets:
          - subnet: "192.168.50.0/24"
            router: "192.168.50.1"
            pools:
              - range-start: "192.168.50.10"
                range-end: "192.168.50.50"
            host-reservations:
              - hw-address: "aa:bb:cc:dd:ee:01"
                ip-address: "192.168.50.100"
                hostname: "switch1"

    # Update ZTP firmware configuration
    - name: Update ZTP config
      juniper.apstra.ztp_config:
        scope: ztp_config
        state: present
        firmware:
          defaults:
            junos-versions:
              - "25.4R1.12"
          junos:
            device-root-password: "Juniper123"
            system-agent-params:
              agent_type: "offbox"
              job_on_create: "install"
              platform: "junos"

    # Change ZTP admin password
    - name: Change password
      juniper.apstra.ztp_config:
        scope: password
        old_password: "OldPass@123"
        new_password: "NewPass@456"

Return Values
-------------

.. raw:: html

  <table border=0 cellpadding=0 class="documentation-table">
      <tr>
          <th>Key</th>
          <th>Returned</th>
          <th>Description</th>
      </tr>
      <tr>
          <td><b>changed</b> (boolean)</td>
          <td>always</td>
          <td>Whether any changes were made.</td>
      </tr>
      <tr>
          <td><b>config</b> (dict)</td>
          <td>when scope is dhcp_configurator or ztp_config</td>
          <td>The current or resulting configuration.</td>
      </tr>
      <tr>
          <td><b>changes</b> (dict)</td>
          <td>when changes were made</td>
          <td>Summary of changes applied.</td>
      </tr>
      <tr>
          <td><b>msg</b> (string)</td>
          <td>always</td>
          <td>Human-readable message describing the outcome.</td>
      </tr>
  </table>

Authors
~~~~~~~

- Prabhanjan KV (@kvp_jnpr)
