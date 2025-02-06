.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.endpoint_policy_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.endpoint_policy module -- Manage endpoint policies in Apstra
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 0.1.33).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.endpoint_policy`.

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

- This module allows you to create, update, and delete endpoint policies and application points in Apstra.


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

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-api_url:

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

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-auth_token:

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

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-body:

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

      Dictionary containing the endpoint policy object details.

      If the body contains an entry named "application\_points", it expected to be a list of dicts, each containing a "if\_name" string and a "used" boolean to be used to patch the application points.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-id"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-id:

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

      Dictionary containing the blueprint and endpoint policy IDs.

      If only the blueprint ID is provided, the module will attempt to find the endpoint policy by label.

      If the label is not provided, but a virtual\_network\_label parameter is given, the label will be used to find the endpoint policy associated with the virtual network with the matching label.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-password"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-password:

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

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-state:

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

      Desired state of the endpoint policy.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"present"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"absent"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-tags"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-tags:

      .. rst-class:: ansible-option-title

      **tags**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-tags" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      List of tags to apply to the endpoint policy.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-username"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-username:

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

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-verify_certificates:

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

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-virtual_network_label"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__parameter-virtual_network_label:

      .. rst-class:: ansible-option-title

      **virtual_network_label**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-virtual_network_label" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The label of the virtual network to find the endpoint policy for. Used if the endpoing policy id and endpoint label are not provided.


      .. raw:: html

        </div>


.. Attributes


.. Notes


.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    - name: Create an endpoint policy (or update it if the label exists)
      juniper.apstra.endpoint_policy:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        body:
          description: "Example routing policy"
          expect_default_ipv4_route: true
          expect_default_ipv6_route: true
          export_policy:
            l2edge_subnets: true
            loopbacks: true
            spine_leaf_links: false
            spine_superspine_links: false
            static_routes: false
          import_policy: "all"
          label: "example_policy"
          policy_type: "user_defined"
        state: present

    - name: Update an endpoint policy
      juniper.apstra.endpoint_policy:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
          endpoint_policy: "AjAuUuVLylXCUgAqaQ"
        body:
          description: "test VN description UPDATE"

    - name: Update an endpoint policy application point
      juniper.apstra.endpoint_policy:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        virtual_network_label: "vn25"
        body:
          application_points:
            - if_name: "xe-0/0/37"
              used: true
        state: present

    - name: Delete an endpoint policy
      juniper.apstra.endpoint_policy:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
          endpoint_policy: "AjAuUuVLylXCUgAqaQ"
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

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__return-changed:

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

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__return-changes:

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
        <div class="ansibleOptionAnchor" id="return-endpoint_policy"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__return-endpoint_policy:

      .. rst-class:: ansible-option-title

      **endpoint_policy**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-endpoint_policy" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The endpoint policy object details.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` on create or update

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`{"description": "Example routing policy", "expect\_default\_ipv4\_route": true, "expect\_default\_ipv6\_route": true, "export\_policy": {"l2edge\_subnets": true, "loopbacks": true, "spine\_leaf\_links": false, "spine\_superspine\_links": false, "static\_routes": false}, "id": "AjAuUuVLylXCUgAqaQ", "import\_policy": "all", "label": "example\_policy", "policy\_type": "user\_defined"}`


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-id"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__return-id:

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

      The ID of the created endpoint policy.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` on create, or when object identified by label

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`{"blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962", "endpoint\_policy": "AjAuUuVLylXCUgAqaQ"}`


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-msg"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__return-msg:

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
        <div class="ansibleOptionAnchor" id="return-response"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__return-response:

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

      The endpoint policy object details.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is present and changes are made


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-tag_response"></div>

      .. _ansible_collections.juniper.apstra.endpoint_policy_module__return-tag_response:

      .. rst-class:: ansible-option-title

      **tag_response**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-tag_response" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The response from applying tags to the endpoint policy.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when tags are applied

      .. rst-class:: ansible-option-line
      .. rst-class:: ansible-option-sample

      :ansible-option-sample-bold:`Sample:` :ansible-rv-sample-value:`["red", "blue"]`


      .. raw:: html

        </div>



..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Edwin Jacques (@edwinpjacques)



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
