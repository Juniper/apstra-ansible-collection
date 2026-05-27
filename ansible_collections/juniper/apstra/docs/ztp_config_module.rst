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

    # =========================================================================
    # DHCP CONFIGURATOR SCOPE — Query, Update, Reservations
    # =========================================================================

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

    # Configure DHCP subnets, pools, options, and host-reservations
    # Shows all available DHCP options
    - name: Configure DHCP with all options
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: present
        options:
          domain-name: "ztplab.local"
          domain-search: "ztplab.local"
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
              - hw-address: "aa:bb:cc:dd:ee:02"
                ip-address: "192.168.50.101"
                hostname: "switch2"
            reservation-mode:
              - "all"

    # Configure multiple DHCP subnets with separate pools
    - name: Configure multiple subnets
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: present
        subnets:
          - subnet: "192.168.50.0/24"
            router: "192.168.50.1"
            pools:
              - range-start: "192.168.50.10"
                range-end: "192.168.50.50"
          - subnet: "10.0.0.0/24"
            router: "10.0.0.1"
            pools:
              - range-start: "10.0.0.10"
                range-end: "10.0.0.100"

    # Add host-reservations to the first existing subnet
    # When subnets are not provided, reservations merge into the first subnet
    - name: Add host reservation
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: present
        host_reservations:
          - hw-address: "aa:bb:cc:dd:ee:03"
            ip-address: "192.168.50.102"
            hostname: "switch3"

    # Add global host reservations (outside any subnet)
    - name: Add global host reservation
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: present
        global_host_reservations:
          - hw-address: "aa:bb:cc:dd:ee:ff"
            ip-address: "10.10.10.100"
            hostname: "global-device"

    # Set default reservation mode
    - name: Set reservation mode
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: present
        reservation_mode_default:
          - "all"

    # Remove a host-reservation by MAC address
    - name: Remove host reservation
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: absent
        host_reservations:
          - hw-address: "aa:bb:cc:dd:ee:03"
            ip-address: "192.168.50.102"

    # Remove an entire subnet
    - name: Remove a subnet
      juniper.apstra.ztp_config:
        scope: dhcp_configurator
        state: absent
        subnets:
          - subnet: "10.0.0.0/24"

    # =========================================================================
    # ZTP CONFIG SCOPE — Query, Update firmware/password/agent settings
    # =========================================================================

    # Query current ZTP JSON config
    - name: Get ZTP firmware config
      juniper.apstra.ztp_config:
        scope: ztp_config
        state: query
      register: ztp_fw

    # Configure complete ZTP JSON with all platform blocks
    # This manages the full ztp.json used by the ZTP VM for provisioning
    - name: Configure complete ZTP JSON
      juniper.apstra.ztp_config:
        scope: ztp_config
        state: present
        firmware:
          defaults:
            device-root-password: "admin"
            device-user: "aosadmin"
            device-user-password: "aosadmin"
            dual-routing-engine: false
            junos-versions:
              - "25.4R1.12"
            junos-evo-image: "http://server/path/to/junos-evo-install.tgz"
            junos-evo-versions:
              - "junos-evo-version1"
            eos-image: "aos_eos_image.bin"
            eos-versions:
              - "eos-version1"
              - "eos-version2"
            nxos-image: "aos_nxos_image.bin"
            nxos-versions:
              - "nxos-version1"
            sonic-image: "http://server/path/to/sonic.bin"
            sonic-versions:
              - "sonic-version1"
              - "sonic-version2"
            management-subnet-prefixlen: 0
            system-agent-params:
              agent_type: "onbox"
          junos:
            device-root-password: "Juniper123"
            device-user-password: "Juniper123"
            system-agent-params:
              agent_type: "offbox"
              job_on_create: "install"
              platform: "junos"
          junos-evo:
            device-root-password: "root123"
            device-user-password: "aosadmin123"
            system-agent-params:
              agent_type: "offbox"
              job_on_create: "install"
              platform: "junos"
          eos:
            custom-config: "eos_custom.sh"
          nxos:
            device-root-password: "admin123"
            system-agent-params:
              agent_type: "onbox"

    # Update only Junos settings (other platforms are preserved)
    # The module does a deep merge — only specified keys are updated
    - name: Update Junos ZTP settings only
      juniper.apstra.ztp_config:
        scope: ztp_config
        state: present
        firmware:
          junos:
            device-root-password: "{{ junos_root_password }}"
            device-user-password: "{{ junos_user_password }}"
            system-agent-params:
              agent_type: "offbox"
              job_on_create: "install"
              platform: "junos"

    # Update default settings only
    - name: Update default ZTP settings
      juniper.apstra.ztp_config:
        scope: ztp_config
        state: present
        firmware:
          defaults:
            device-root-password: "{{ default_root_password }}"
            device-user: "{{ device_user }}"
            device-user-password: "{{ device_user_password }}"
            junos-versions:
              - "25.4R1.12"

    # =========================================================================
    # PASSWORD SCOPE — Change ZTP web UI admin password
    # =========================================================================

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
