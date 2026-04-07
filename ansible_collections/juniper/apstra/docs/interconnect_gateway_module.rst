.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.interconnect_gateway_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.interconnect_gateway module -- Manage EVPN Interconnect Domains and their Gateways in Apstra blueprints
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.0.6).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.interconnect_gateway`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 0.2.0

.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- This module manages both EVPN Interconnect Domains and Interconnect Domain Gateways within an Apstra blueprint.
- Use ``type=domain`` to manage Interconnect Domains (EVPN Interconnect Groups) that group sites for EVPN-based DCI.
- Use ``type=gateway`` (the default) to manage Interconnect Domain Gateways — remote EVPN gateways linked to an Interconnect Domain.
- The equivalent Terraform resources are ``apstra_datacenter_interconnect_domain`` and ``apstra_datacenter_interconnect_domain_gateway``.


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

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-api_url:

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

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-auth_token:

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
        <div class="ansibleOptionAnchor" id="parameter-body"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-body:

      .. rst-class:: ansible-option-title

      **body**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-body" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Dictionary containing the resource details.

      **For type=domain:**

      - ``label`` (string) — Domain name (required for create).
      - ``route_target`` (string) — Interconnect Route Target in ``<asn>:<nn>`` format (required for create).
      - ``esi_mac`` (string) — Optional per-site ESI MAC address.

      **For type=gateway:**

      - ``gw_name`` (string) — Gateway name (required for create).
      - ``gw_ip`` (string) — Gateway IPv4 address (required for create).
      - ``gw_asn`` (integer) — Gateway AS number, 1–4294967295 (required for create).
      - ``local_gw_nodes`` (list) — IDs or labels of leaf switches that peer with this gateway (required for create). System labels are resolved automatically to graph node UUIDs.
      - ``evpn_interconnect_group_id`` (string) — ID or label of the parent Interconnect Domain (required for create). Domain labels are resolved automatically.
      - ``ttl`` (integer) — BGP TTL in hops (optional).
      - ``keepalive_timer`` (integer) — BGP keepalive in seconds (optional).
      - ``holdtime_timer`` (integer) — BGP hold time in seconds (optional).
      - ``password`` (string) — BGP session password (optional).


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-id"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-id:

      .. rst-class:: ansible-option-title

      **id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-id" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Dictionary containing the blueprint and resource IDs.

      ``blueprint`` is always required (name or UUID).

      **For type=domain:** ``evpn_interconnect_group`` is optional for create (looked up by ``label`` for idempotency), required for explicit update/delete.

      **For type=gateway:** ``remote_gateway`` is optional for create (looked up by ``gw_name`` for idempotency), required for explicit update/delete.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-password"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-password:

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
        <div class="ansibleOptionAnchor" id="parameter-state"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-state:

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

      Desired state of the resource.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"present"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"absent"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-type"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-type:

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

      The type of interconnect resource to manage.

      ``domain`` manages Interconnect Domains (EVPN Interconnect Groups). Body fields are ``label``, ``route_target``, and optional ``esi_mac``.

      ``gateway`` manages Interconnect Domain Gateways (remote gateways linked to a domain). Body fields are ``gw_name``, ``gw_ip``, ``gw_asn``, ``local_gw_nodes``, and ``evpn_interconnect_group_id``.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`"domain"`
      - :ansible-option-choices-entry-default:`"gateway"` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-username"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-username:

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

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__parameter-verify_certificates:

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

Notes
-----

.. note::

   - Blueprint names are resolved to UUIDs automatically. You can pass either the blueprint label or its UUID in ``id.blueprint``.
   - For ``type=gateway``, system labels in ``local_gw_nodes`` are resolved to graph node UUIDs automatically.
   - For ``type=gateway``, the ``evpn_interconnect_group_id`` field accepts either a domain label or its UUID.
   - Domain lookup by ``label`` and gateway lookup by ``gw_name`` provide create-or-update idempotency without needing to supply explicit IDs.


.. Seealso

See Also
--------

.. seealso::

   :ref:`juniper.apstra.routing_policy <ansible_collections.juniper.apstra.routing_policy_module>`
       Manage routing policies in Apstra.
   :ref:`juniper.apstra.virtual_network <ansible_collections.juniper.apstra.virtual_network_module>`
       Manage virtual networks in Apstra.
   :ref:`juniper.apstra.security_zone <ansible_collections.juniper.apstra.security_zone_module>`
       Manage security zones in Apstra.


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    # ---- Interconnect Domain (type: domain) ----

    # Create an Interconnect Domain (blueprint may be name or UUID)
    - name: Create interconnect domain
      juniper.apstra.interconnect_gateway:
        type: domain
        id:
          blueprint: "my-datacenter-blueprint"
        body:
          label: "dci-domain-1"
          route_target: "65500:100"
        state: present
      register: icd

    # Create domain with ESI MAC
    - name: Create interconnect domain with ESI MAC
      juniper.apstra.interconnect_gateway:
        type: domain
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          label: "dci-domain-2"
          route_target: "65500:200"
          esi_mac: "02:00:00:00:00:01"
        state: present

    # Update a domain by label (no ID needed - looked up automatically)
    - name: Update interconnect domain by label
      juniper.apstra.interconnect_gateway:
        type: domain
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          label: "dci-domain-1"
          route_target: "65500:102"
        state: present

    # Delete a domain by label (no evpn_interconnect_group ID needed)
    - name: Delete interconnect domain by label
      juniper.apstra.interconnect_gateway:
        type: domain
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          label: "dci-domain-2"
        state: absent

    # ---- Interconnect Domain Gateway (type: gateway) ----

    # Create a gateway using system labels and domain label
    - name: Create interconnect gateway using labels
      juniper.apstra.interconnect_gateway:
        id:
          blueprint: "my-datacenter-blueprint"
        body:
          gw_name: "remote-dc2-gw"
          gw_ip: "10.1.0.1"
          gw_asn: 65500
          evpn_interconnect_group_id: "dci-domain-1"
          local_gw_nodes:
            - "border-leaf-1"
            - "border-leaf-2"
          ttl: 2
          keepalive_timer: 10
          holdtime_timer: 30
        state: present
      register: icgw

    # Update a gateway by name lookup (no remote_gateway ID needed)
    - name: Update interconnect gateway by gw_name
      juniper.apstra.interconnect_gateway:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          gw_name: "remote-dc2-gw"
          gw_ip: "10.1.0.3"
          gw_asn: 65500
          evpn_interconnect_group_id: "dci-domain-1"
          local_gw_nodes:
            - "border-leaf-1"
        state: present

    # Delete an interconnect gateway by ID
    - name: Delete interconnect gateway
      juniper.apstra.interconnect_gateway:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
          remote_gateway: "{{ icgw.id.remote_gateway }}"
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

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__return-changed:

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
        <div class="ansibleOptionAnchor" id="return-changes"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__return-changes:

      .. rst-class:: ansible-option-title

      **changes**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-changes" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Dictionary of updates that were applied.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` on update


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-evpn_interconnect_group"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__return-evpn_interconnect_group:

      .. rst-class:: ansible-option-title

      **evpn_interconnect_group**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-evpn_interconnect_group" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The interconnect domain object (type=domain).


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when type=domain and state=present

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`{"id": "r\_TDcZaG24I1ywU5jw", "interconnect\_esi\_mac": "02:ff:00:00:00:01", "interconnect\_route\_target": "65500:100", "interconnect\_security\_zones": {}, "interconnect\_virtual\_networks": {}, "label": "dci-domain-1", "remote\_gateway\_node\_ids": {}}`


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-id"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__return-id:

      .. rst-class:: ansible-option-title

      **id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-id" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The ID dictionary. For type=domain contains ``blueprint`` and ``evpn_interconnect_group``. For type=gateway contains ``blueprint`` and ``remote_gateway``.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` on create, or when object identified by label/gw\_name

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`{"blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962", "evpn\_interconnect\_group": "r\_TDcZaG24I1ywU5jw"}`


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-msg"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__return-msg:

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


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-remote_gateway"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__return-remote_gateway:

      .. rst-class:: ansible-option-title

      **remote_gateway**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-remote_gateway" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The interconnect gateway object (type=gateway).


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when type=gateway and state=present

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`{"evpn\_interconnect\_group\_id": "r\_TDcZaG24I1ywU5jw", "gw\_asn": 65500, "gw\_ip": "10.1.0.1", "gw\_name": "remote-dc2-gw", "holdtime\_timer": 30, "id": "abc123", "keepalive\_timer": 10, "local\_gw\_nodes": [{"node\_id": "PPbnMs25oIuO8WHldA"}], "ttl": 2}`


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-response"></div>

      .. _ansible_collections.juniper.apstra.interconnect_gateway_module__return-response:

      .. rst-class:: ansible-option-title

      **response**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-response" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The resource object details.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is present and changes are made


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
  - title: "Repository (Sources)"
    url: "https://github.com/Juniper/apstra-ansible-collection"
    external: true
