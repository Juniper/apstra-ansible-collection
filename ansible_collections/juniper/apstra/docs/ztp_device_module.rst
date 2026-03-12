.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.ztp_device_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.ztp_device module -- Manage ZTP devices in Apstra
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_.

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.ztp_device`.

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

- This module allows you to create, delete, and check the status of ZTP (Zero Touch Provisioning) devices in Apstra.
- ZTP devices are managed via the ``/api/ztp/device`` API endpoint.
- Device status can be retrieved using the ``/api/ztp/device/{ip_addr}/status`` API endpoint by setting ``state`` to ``status``.
- Status can be looked up by either ``ip_addr`` or ``system_id``. The module fails if the device is not registered.
- The ZTP device API does not support individual GET or PUT/PATCH operations. Updates are performed by deleting and recreating the device.
- The module uses the Apstra SDK when available, falling back to direct API calls if necessary.

.. Aliases

.. Requirements

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

      .. _ansible_collections.juniper.apstra.ztp_device_module__parameter-api_url:

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

      :ansible-option-default-bold:`Default:` :ansible-option-default:`APSTRA\_API\_URL environment variable`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-verify_certificates"></div>

      .. _ansible_collections.juniper.apstra.ztp_device_module__parameter-verify_certificates:

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

      :ansible-option-default-bold:`Default:` :ansible-option-default:`true`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-id"></div>

      .. _ansible_collections.juniper.apstra.ztp_device_module__parameter-id:

      .. rst-class:: ansible-option-title

      **id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-id" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Dictionary containing the ZTP device identifier.

      ``ip_addr`` is the management IP address of the device.

      ``system_id`` is the system identifier of the device.

      For ``status``, provide either ``ip_addr`` or ``system_id``. If only ``system_id`` is given, the module resolves the IP by listing all registered devices.

      For ``absent``, ``ip_addr`` is required. For create, ``ip_addr`` can be provided in the ``body`` instead.

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-body"></div>

      .. _ansible_collections.juniper.apstra.ztp_device_module__parameter-body:

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

      Dictionary containing the ZTP device details.

      Used for create and update operations.

      ``ip_addr`` (string) - Management IP address of the device (required for create).

      ``system_id`` (string) - System identifier for the device (required for create).

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-state"></div>

      .. _ansible_collections.juniper.apstra.ztp_device_module__parameter-state:

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

      Desired state of the ZTP device.

      ``present`` will create the device (or update via delete+recreate).

      ``absent`` will delete the device.

      ``status`` will retrieve the ZTP provisioning status of the device (requires ``ip_addr`` or ``system_id`` in ``id``). Fails if the device is not registered.

      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"present"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"absent"`
      - :ansible-option-choices-entry:`"status"`

      .. raw:: html

        </div>

Examples
--------

.. code-block:: yaml+jinja

    # Check ZTP device status by IP address
    # Module fails if the IP address is not registered
    - name: Get ZTP device status by IP
      juniper.apstra.ztp_device:
        id:
          ip_addr: "192.168.50.10"
        state: status
      register: ztp_status

    - name: Show provisioning status (completed / unknown / in_progress)
      ansible.builtin.debug:
        msg: "ZTP status is {{ ztp_status.status }}"

    # Check ZTP device status by system_id
    # Module fails if no device with that system_id is registered
    - name: Get ZTP device status by system_id
      juniper.apstra.ztp_device:
        id:
          system_id: "device-001"
        state: status
      register: ztp_status

    - name: Show full ZTP device details
      ansible.builtin.debug:
        var: ztp_status.ztp_device

Return Values
-------------

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

        </a>

      .. ansible-option-type-line::

        :ansible-return-type:`boolean`

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
        <div class="ansibleOptionAnchor" id="return-ztp_device"></div>

      .. rst-class:: ansible-option-title

      **ztp_device**

      .. raw:: html

        </a>

      .. ansible-option-type-line::

        :ansible-return-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The ZTP device object details retrieved from the status endpoint.

      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` on create, update, or status check

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-ztp_devices"></div>

      .. rst-class:: ansible-option-title

      **ztp_devices**

      .. raw:: html

        </a>

      .. ansible-option-type-line::

        :ansible-return-type:`list`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      List of all registered ZTP devices.

      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is present with no id and no body

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-status"></div>

      .. rst-class:: ansible-option-title

      **status**

      .. raw:: html

        </a>

      .. ansible-option-type-line::

        :ansible-return-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The ZTP provisioning status string of the device.
      One of ``completed``, ``unknown``, or ``in_progress``.
      The module fails with an error if the device is not registered.

      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is status

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-msg"></div>

      .. rst-class:: ansible-option-title

      **msg**

      .. raw:: html

        </a>

      .. ansible-option-type-line::

        :ansible-return-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The output message that the module generates.

      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` always

      .. raw:: html

        </div>
