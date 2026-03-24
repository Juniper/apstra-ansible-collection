.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.interconnect_domain_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.interconnect_domain module -- Manage EVPN Interconnect Domains in Apstra blueprints
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.0.5).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible\-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.interconnect_domain`.

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

- This module allows you to create, update, and delete EVPN Interconnect Domains (called ``evpn_interconnect_group`` in the Apstra API) within an Apstra blueprint.
- An Interconnect Domain groups sites together for EVPN-based DCI (Data Centre Interconnect).
- Every gateway in the domain must share the same Interconnect Route Target (iRT).
- Optionally, a per-site ESI MAC can be set to generate unique iESI values at the MAC-VRF level.
- This module operates at the blueprint scope and requires a Datacenter (two\_stage\_l3clos) design.
- An Interconnect Domain is a prerequisite for the Interconnect Domain Gateway.
- The equivalent Terraform resource is ``apstra_datacenter_interconnect_domain``.


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

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-api_url:

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

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-auth_token:

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

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-body:

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

      Dictionary containing the EVPN Interconnect Domain details.

      :literal:`label` (string) \- Human\-readable name for the domain (required for create).

      :literal:`route\_target` (string) \- The Interconnect Route Target (iRT) shared by all gateways in the domain. Format is typically :literal:`\<asn\>:\<nn\>` (required for create).

      :literal:`esi\_mac` (string) \- Optional per\-site ESI MAC address used to generate unique iESI values at the MAC\-VRF level.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-id"></div>

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-id:

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

      Dictionary containing the blueprint and interconnect domain IDs.

      :literal:`blueprint` is always required.

      :literal:`evpn\_interconnect\_group` is optional for create (looked up by :literal:`label` from :literal:`body` for idempotency), required for update/delete.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-password"></div>

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-password:

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

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-state:

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

      Desired state of the interconnect domain.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"present"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"absent"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-username"></div>

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-username:

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

      .. _ansible_collections.juniper.apstra.interconnect_domain_module__parameter-verify_certificates:

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

    # Create an EVPN Interconnect Domain
    - name: Create interconnect domain
      juniper.apstra.interconnect_domain:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          label: "dci-domain-1"
          route_target: "65500:100"
        state: present
      register: icd

    # Create with ESI MAC
    - name: Create interconnect domain with ESI MAC
      juniper.apstra.interconnect_domain:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          label: "dci-domain-2"
          route_target: "65500:200"
          esi_mac: "02:00:00:00:00:01"
        state: present
      register: icd_esi

    # Update an interconnect domain
    - name: Update interconnect domain route_target
      juniper.apstra.interconnect_domain:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
          evpn_interconnect_group: "{{ icd.id.evpn_interconnect_group }}"
        body:
          label: "dci-domain-1"
          route_target: "65500:101"
        state: present

    # Update by label lookup (idempotent)
    - name: Update interconnect domain by label
      juniper.apstra.interconnect_domain:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          label: "dci-domain-1"
          route_target: "65500:102"
        state: present

    # Delete an interconnect domain
    - name: Delete interconnect domain
      juniper.apstra.interconnect_domain:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
          evpn_interconnect_group: "{{ icd.id.evpn_interconnect_group }}"
        state: absent


.. Return Values

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

      :ansible-rv-samplevalue-bold:`Sample:` :ansible-rv-samplevalue:`true`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-changes"></div>

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

      :ansible-rv-returned-bold:`Returned:` on update

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-evpn_interconnect_group"></div>

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

      The interconnect domain object details.


      .. rst-class:: ansible-option-line

      :ansible-rv-returned-bold:`Returned:` on create or update

      .. rst-class:: ansible-option-line

      :ansible-rv-samplevalue-bold:`Sample:` :ansible-rv-samplevalue:`{"esi\_mac": null, "id": "aB3xYz12KgV2mbYopw", "label": "dci\-domain\-1", "route\_target": "65500:100"}`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-id"></div>

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

      The ID dictionary of the interconnect domain.


      .. rst-class:: ansible-option-line

      :ansible-rv-returned-bold:`Returned:` on create, or when object identified by label

      .. rst-class:: ansible-option-line

      :ansible-rv-samplevalue-bold:`Sample:` :ansible-rv-samplevalue:`{"blueprint": "5f2a77f6\-1f33\-4e11\-8d59\-6f9c26f16962", "evpn\_interconnect\_group": "aB3xYz12KgV2mbYopw"}`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-msg"></div>

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

      :ansible-rv-returned-bold:`Returned:` always

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-response"></div>

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

      The interconnect domain object details.


      .. rst-class:: ansible-option-line

      :ansible-rv-returned-bold:`Returned:` when state is present and changes are made

      .. raw:: html

        </div>


.. Status (Coverage)

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

.. Parsing errors
