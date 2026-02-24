.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.connectivity_template_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.connectivity_template module -- Manage Connectivity Templates in Apstra blueprints
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.0.5).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible\-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.connectivity_template`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 0.1.0

.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- This module allows you to create, update, and delete Connectivity Templates (CTs) within an Apstra blueprint.
- A Connectivity Template is a declarative specification of network primitives (IP Link, BGP Peering, Routing Policy, etc.) that can be assigned to application points (interfaces, SVIs, loopbacks, protocol endpoints, or systems).
- Every CT has a :strong:`type` that determines which primitives may be used and which kind of application point it targets.
- Primitives are specified as a dict\-of\-named\-dicts keyed by the :strong:`plural` primitive type name. Child primitives are nested inside their parent as additional dict keys.
- The module automatically builds the internal batch/pipeline/primitive hierarchy required by the Apstra API.
- Idempotent by :literal:`name`. If a CT with the same name already exists, the module compares the desired primitives with the current state (via :literal:`obj\-policy\-export`\ ) and updates only when there are differences.
- This module manages the CT definition only. Use the :literal:`connectivity\_template\_assignment` module to assign CTs to application points.


.. Aliases


.. Requirements






.. Options

Parameters
----------

.. tabularcolumns:: \X{1}{3}\X{2}{3}

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1
  :class: longtable ansible-option-table

  * - Parameter
    - Comments

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-api_url"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-api_url:

      .. rst-class:: ansible-option-title

      **api_url**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-api_url" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The URL used to access the Apstra api.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_API\_URL environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-auth_token"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-auth_token:

      .. rst-class:: ansible-option-title

      **auth_token**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-auth_token" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The authentication token to use if already authenticated.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_AUTH\_TOKEN environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-blueprint_id"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-blueprint_id:

      .. rst-class:: ansible-option-title

      **blueprint_id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-blueprint_id" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The ID of the Apstra blueprint.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-ct_id"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-ct_id:

      .. rst-class:: ansible-option-title

      **ct_id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-ct_id" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The UUID of an existing Connectivity Template.

      When provided, the module operates on this specific CT instead of looking up by :literal:`name`.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-description"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-description:

      .. rst-class:: ansible-option-title

      **description**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-description" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      An optional description for the Connectivity Template.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`""`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-name"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-name:

      .. rst-class:: ansible-option-title

      **name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The display name of the Connectivity Template.

      Used as the unique identifier for idempotent operations.

      Required when :literal:`state=present`.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-password"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-password:

      .. rst-class:: ansible-option-title

      **password**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-password" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The password for authentication.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_PASSWORD environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-primitives"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-primitives:

      .. rst-class:: ansible-option-title

      **primitives**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-primitives" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      A dict\-of\-named\-dicts keyed by :strong:`plural` primitive type name.

      Each top\-level key is a primitive type (e.g. :literal:`ip\_links`\ , :literal:`virtual\_network\_singles`\ , :literal:`bgp\_peering\_generic\_systems`\ ).

      Under each type key is a dict of named instances.

      Each instance is a dict of type\-specific attributes passed directly to the Apstra API.

      Child primitives are nested as additional dict keys using their plural type name (e.g. :literal:`bgp\_peering\_generic\_systems` inside an :literal:`ip\_links` instance).

      Supported primitive types: :literal:`ip\_links`\ , :literal:`virtual\_network\_singles`\ , :literal:`virtual\_network\_multiples`\ , :literal:`bgp\_peering\_generic\_systems`\ , :literal:`bgp\_peering\_ip\_endpoints`\ , :literal:`routing\_policies`\ , :literal:`static\_routes`\ , :literal:`custom\_static\_routes`\ , :literal:`dynamic\_bgp\_peerings`\ , :literal:`routing\_zone\_constraints`.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-state"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-state:

      .. rst-class:: ansible-option-title

      **state**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-state" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Desired state of the Connectivity Template.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"present"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"absent"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-tags"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-tags:

      .. rst-class:: ansible-option-title

      **tags**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-tags" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      A list of tags to apply to the CT.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-type"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-type:

      .. rst-class:: ansible-option-title

      **type**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-type" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The type of Connectivity Template, which determines which primitives are allowed and which application point type the CT targets.

      Required when :literal:`state=present`.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`"interface"`
      - :ansible-option-choices-entry:`"svi"`
      - :ansible-option-choices-entry:`"loopback"`
      - :ansible-option-choices-entry:`"protocol\_endpoint"`
      - :ansible-option-choices-entry:`"system"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-username"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-username:

      .. rst-class:: ansible-option-title

      **username**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-username" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The username for authentication.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_USERNAME environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-verify_certificates"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__parameter-verify_certificates:

      .. rst-class:: ansible-option-title

      **verify_certificates**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-verify_certificates" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      If set to false, SSL certificates will not be verified.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`false`
      - :ansible-option-choices-entry-default:`true` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>


.. Attributes


.. Notes


.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    # ── Interface CT type examples ────────────────────────────────────────

    # Interface CT: IP Link + BGP Peering + Routing Policy (full nesting)
    - name: Create BGP-to-SRX Connectivity Template
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "BGP-2-SRX"
        type: interface
        description: "CT for external router connectivity"
        tags:
          - prod
          - border
        primitives:
          ip_links:
            srx_link:
              security_zone: "{{ routing_zone_id }}"
              interface_type: tagged
              vlan_id: 100
              ipv4_addressing_type: numbered
              ipv6_addressing_type: none
              bgp_peering_generic_systems:
                srx_peer:
                  bfd: false
                  ipv4_safi: true
                  ipv6_safi: false
                  ttl: 2
                  session_addressing_ipv4: addressed
                  session_addressing_ipv6: link_local
                  peer_from: interface
                  peer_to: interface_or_ip_endpoint
                  neighbor_asn_type: dynamic
                  routing_policies:
                    default_rp:
                      rp_to_attach: "{{ routing_policy_id }}"
        state: present
      register: ct_result

    # Interface CT: IP Link with Static Route child
    - name: Create IP Link with Static Route CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Static-Route-Link"
        type: interface
        primitives:
          ip_links:
            static_link:
              security_zone: "{{ routing_zone_id }}"
              interface_type: tagged
              vlan_id: 200
              ipv4_addressing_type: numbered
              ipv6_addressing_type: none
              static_routes:
                default_route:
                  network: "0.0.0.0/0"
                  share_ip_endpoint: false
                  routing_policies:
                    static_rp: {}
        state: present

    # Interface CT: IP Link with Custom Static Route child
    - name: Create IP Link with Custom Static Route CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Custom-Static-Link"
        type: interface
        primitives:
          ip_links:
            custom_link:
              security_zone: "{{ routing_zone_id }}"
              interface_type: untagged
              ipv4_addressing_type: numbered
              ipv6_addressing_type: none
              custom_static_routes:
                mgmt_route:
                  network: "10.0.0.0/8"
                  next_hop: next_hop_ip
        state: present

    # Interface CT: IP Link with Routing Policy (direct — no BGP/static in between)
    - name: Create IP Link with direct Routing Policy CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "IP-Link-Direct-RP"
        type: interface
        primitives:
          ip_links:
            direct_rp_link:
              security_zone: "{{ routing_zone_id }}"
              interface_type: tagged
              vlan_id: 150
              ipv4_addressing_type: numbered
              ipv6_addressing_type: none
              routing_policies:
                export_filter:
                  rp_to_attach: "{{ routing_policy_id }}"
        state: present

    # Interface CT: Virtual Network (Single) — simple VLAN access
    - name: Create VN Single CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "VLAN-100-Access"
        type: interface
        primitives:
          virtual_network_singles:
            vlan100:
              vn_node_id: "{{ virtual_network_id }}"
        state: present

    # Interface CT: Virtual Network (Multiple) — trunk with multiple VLANs
    - name: Create VN Multiple CT (trunk)
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Trunk-VLANs"
        type: interface
        primitives:
          virtual_network_multiples:
            trunk_vlans:
              tagged_vn_node_ids:
                - "{{ vn_id_1 }}"
                - "{{ vn_id_2 }}"
              untagged_vn_node_id: "{{ native_vn_id }}"
        state: present

    # Interface CT: Routing Zone Constraint
    - name: Create Routing Zone Constraint CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "RZ-Constraint-Intf"
        type: interface
        primitives:
          routing_zone_constraints:
            allow_default_only:
              routing_zone_constraint_mode: allow
              constraints:
                - "{{ routing_zone_id }}"
        state: present

    # Interface CT: Custom Static Route (top-level)
    - name: Create Custom Static Route CT for interface
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Custom-Static-Intf"
        type: interface
        primitives:
          custom_static_routes:
            default_gw:
              network: "0.0.0.0/0"
              next_hop: next_hop_ip
        state: present

    # Interface CT: Multiple primitives in one CT
    - name: Create CT with both IP Link and Routing Zone Constraint
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Multi-Primitive-CT"
        type: interface
        primitives:
          ip_links:
            server_link:
              security_zone: "{{ routing_zone_id }}"
              interface_type: tagged
              vlan_id: 300
              ipv4_addressing_type: numbered
              ipv6_addressing_type: none
          routing_zone_constraints:
            rz_limit:
              routing_zone_constraint_mode: allow
              constraints:
                - "{{ routing_zone_id }}"
        state: present

    # ── SVI CT type examples ─────────────────────────────────────────────

    # SVI CT: BGP Peering (Generic System) with Routing Policy
    - name: Create SVI BGP CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "SVI-BGP-Peering"
        type: svi
        primitives:
          bgp_peering_generic_systems:
            external_peer:
              bfd: true
              ipv4_safi: true
              ipv6_safi: false
              ttl: 2
              session_addressing_ipv4: addressed
              session_addressing_ipv6: link_local
              peer_from: interface
              peer_to: interface_or_ip_endpoint
              neighbor_asn_type: dynamic
              routing_policies:
                export_rp:
                  rp_to_attach: "{{ routing_policy_id }}"
        state: present

    # SVI CT: Dynamic BGP Peering
    - name: Create SVI Dynamic BGP CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "SVI-Dynamic-BGP"
        type: svi
        primitives:
          dynamic_bgp_peerings:
            auto_peer:
              ipv4_enabled: true
              ipv6_enabled: false
              ttl: 1
              session_addressing_ipv4: addressed
              session_addressing_ipv6: link_local
              bfd: false
              password: ""
              routing_policies:
                bgp_rp: {}
        state: present

    # SVI CT: Static Route
    - name: Create SVI Static Route CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "SVI-Static-Route"
        type: svi
        primitives:
          static_routes:
            default_route:
              network: "0.0.0.0/0"
              share_ip_endpoint: false
        state: present

    # SVI CT: Virtual Network (Single)
    - name: Create SVI VN Single CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "SVI-VN-Single"
        type: svi
        primitives:
          virtual_network_singles:
            svi_vlan:
              vn_node_id: "{{ virtual_network_id }}"
        state: present

    # SVI CT: Routing Zone Constraint
    - name: Create SVI Routing Zone Constraint CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "SVI-RZ-Constraint"
        type: svi
        primitives:
          routing_zone_constraints:
            svi_rz_limit:
              routing_zone_constraint_mode: deny
              constraints:
                - "{{ routing_zone_id }}"
        state: present

    # ── Loopback CT type examples ────────────────────────────────────────

    # Loopback CT: BGP Peering (IP Endpoint) with Routing Policy
    - name: Create Loopback BGP IP Endpoint CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Loopback-BGP"
        type: loopback
        primitives:
          bgp_peering_ip_endpoints:
            lo0_peer:
              ipv4_safi: true
              ipv6_safi: false
              bfd: false
              ttl: 2
              session_addressing_ipv4: addressed
              session_addressing_ipv6: link_local
              password: ""
              routing_policies:
                lo_rp: {}
        state: present

    # Loopback CT: Static Route
    - name: Create Loopback Static Route CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Loopback-Static"
        type: loopback
        primitives:
          static_routes:
            lo_static:
              network: "192.168.1.0/24"
              share_ip_endpoint: false
        state: present

    # Loopback CT: Routing Zone Constraint
    - name: Create Loopback Routing Zone Constraint CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Loopback-RZ-Constraint"
        type: loopback
        primitives:
          routing_zone_constraints:
            lo_rz_limit:
              routing_zone_constraint_mode: allow
              constraints:
                - "{{ routing_zone_id }}"
        state: present

    # ── Protocol Endpoint CT type examples ───────────────────────────────

    # Protocol Endpoint CT: BGP Peering (IP Endpoint)
    - name: Create Protocol Endpoint BGP CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Proto-EP-BGP"
        type: protocol_endpoint
        primitives:
          bgp_peering_ip_endpoints:
            ep_peer:
              ipv4_safi: true
              ipv6_safi: false
              bfd: true
              ttl: 1
              session_addressing_ipv4: addressed
              session_addressing_ipv6: link_local
              routing_policies:
                ep_rp:
                  rp_to_attach: "{{ routing_policy_id }}"
        state: present

    # Protocol Endpoint CT: Routing Zone Constraint
    - name: Create Protocol Endpoint RZ Constraint CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "Proto-EP-RZ-Constraint"
        type: protocol_endpoint
        primitives:
          routing_zone_constraints:
            ep_rz_limit:
              routing_zone_constraint_mode: allow
              constraints:
                - "{{ routing_zone_id }}"
        state: present

    # ── System CT type examples ──────────────────────────────────────────

    # System CT: Custom Static Route
    - name: Create System Custom Static Route CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "System-Static-Route"
        type: system
        primitives:
          custom_static_routes:
            sys_default:
              network: "0.0.0.0/0"
              next_hop: next_hop_ip
              routing_policies:
                sys_rp: {}
        state: present

    # ── Update and delete examples ───────────────────────────────────────

    # Update an existing CT by name (idempotent — re-run detects no change)
    - name: Update BGP-2-SRX CT (change VLAN)
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "BGP-2-SRX"
        type: interface
        description: "Updated CT — new VLAN"
        primitives:
          ip_links:
            srx_link:
              security_zone: "{{ routing_zone_id }}"
              interface_type: tagged
              vlan_id: 200
              ipv4_addressing_type: numbered
              ipv6_addressing_type: none
        state: present

    # Delete a CT by name
    - name: Delete Connectivity Template by name
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "BGP-2-SRX"
        state: absent

    # Delete a CT by ID (using registered output from create)
    - name: Delete Connectivity Template by ID
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        ct_id: "{{ ct_result.ct_id }}"
        state: absent



.. Facts


.. Return values

Return Values
-------------
Common return values are documented :ref:`here <common_return_values>`, the following are the fields unique to this module:

.. tabularcolumns:: \X{1}{3}\X{2}{3}

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1
  :class: longtable ansible-option-table

  * - Key
    - Description

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-changed"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-changed:

      .. rst-class:: ansible-option-title

      **changed**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-changed" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Indicates whether the module has made any changes.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` always


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-connectivity_template"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-connectivity_template:

      .. rst-class:: ansible-option-title

      **connectivity_template**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-connectivity_template" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The parsed Connectivity Template object.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is present


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-connectivity_template/description"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-connectivity_template/description:

      .. rst-class:: ansible-option-title

      **description**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-connectivity_template/description" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The CT description.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` success


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-connectivity_template/name"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-connectivity_template/name:

      .. rst-class:: ansible-option-title

      **name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-connectivity_template/name" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The CT display name.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` success


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-connectivity_template/primitives"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-connectivity_template/primitives:

      .. rst-class:: ansible-option-title

      **primitives**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-connectivity_template/primitives" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The primitives in dict\-of\-named\-dicts format.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` success


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-connectivity_template/tags"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-connectivity_template/tags:

      .. rst-class:: ansible-option-title

      **tags**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-connectivity_template/tags" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      Tags applied to the CT.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` success


      .. raw:: html

        </div>



  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-ct_id"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-ct_id:

      .. rst-class:: ansible-option-title

      **ct_id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-ct_id" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The UUID of the Connectivity Template.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is present

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`"b016fec0\-b439\-45a4\-bcf4\-94b481f6005e"`


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-msg"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_module__return-msg:

      .. rst-class:: ansible-option-title

      **msg**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-msg" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The output message that the module generates.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` always


      .. raw:: html

        </div>



..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Juniper Networks


.. Extra links

Collection links
~~~~~~~~~~~~~~~~

.. ansible-links::

  - title: "Issue Tracker"
    url: "https://github.com/Juniper/apstra-ansible-collection/issues"
    external: true
  - title: "Homepage"
    url: "https://www.juniper.net/us/en/products/network-automation/apstra.html"
    external: true
  - title: "Repository (Sources)"
    url: "https://github.com/Juniper/apstra-ansible-collection"
    external: true


.. Parsing errors
