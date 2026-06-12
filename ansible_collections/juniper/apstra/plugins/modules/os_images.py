# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: os_images
short_description: Manage NOS images in Apstra's global device-OS image store
version_added: "1.0.0"
description:
  - Uploads, deletes, and lists NOS (Network OS) images stored in the Apstra
    global image repository at C(/device-os/images).
  - C(state=present) — Upload an image if an image with the same name does not
    already exist (idempotent).
  - C(state=absent) — Delete an image by name or UUID.
  - C(state=gathered) — List all images without making changes.
options:
  id:
    description:
      - Identifies the target image.
      - Used by C(state=absent) to locate the image to delete.
    type: dict
    suboptions:
      image_name:
        description:
          - The file name of the image (e.g. C(junos-23.4R1.tgz)).  Used for
            idempotency checks and delete lookups.
        type: str
      image_id:
        description:
          - UUID of the image.  Takes precedence over C(image_name) when both
            are provided.
        type: str
  body:
    description:
      - Parameters for upload (C(state=present)).
    type: dict
    suboptions:
      image_path:
        description:
          - Local path to the NOS image file to upload.
          - Required for C(state=present).
        type: str
      description:
        description:
          - Human-readable description stored alongside the image.
        type: str
      platform:
        description:
          - Device platform identifier (e.g. C(junos), C(eos), C(nxos)).
        type: str
      image_type:
        description:
          - Image type as expected by Apstra (e.g. C(full)).
        type: str
        default: full
  state:
    description:
      - Desired operation.
      - C(present) — Upload the image if it does not already exist.
      - C(absent) — Delete the image.
      - C(gathered) — Return the list of all images without making changes.
    type: str
    required: true
    choices: ["present", "absent", "gathered"]
notes:
  - Large image files are streamed to the Apstra API in a single multipart
    POST request.  Ensure the Ansible controller has sufficient disk space and
    network bandwidth for the upload.
  - Check mode is supported for C(state=present) and C(state=absent).
extends_documentation_fragment:
  - juniper.apstra.apstra_client
author:
  - Juniper Networks
"""

EXAMPLES = r"""
# List all images
- name: List NOS images
  juniper.apstra.os_images:
    state: gathered

# Upload an image (idempotent — no-op if already present)
- name: Upload Junos image
  juniper.apstra.os_images:
    body:
      image_path: /tmp/junos-23.4R1.tgz
      description: "Junos 23.4R1 for QFX10008"
      platform: junos
    state: present

# Delete an image by name
- name: Remove old Junos image
  juniper.apstra.os_images:
    id:
      image_name: junos-23.4R1.tgz
    state: absent

# Delete an image by UUID
- name: Remove image by UUID
  juniper.apstra.os_images:
    id:
      image_id: "a1b2c3d4-0000-0000-0000-000000000001"
    state: absent
"""

RETURN = r"""
changed:
  description: True when an image was uploaded or deleted.
  type: bool
  returned: always
msg:
  description: Human-readable status message.
  type: str
  returned: always
images:
  description: List of all NOS images returned by the API.
  type: list
  elements: dict
  returned: when state=gathered
image:
  description: Details of the uploaded image.
  type: dict
  returned: when state=present and image was uploaded
image_id:
  description: UUID of the image that was deleted.
  type: str
  returned: when state=absent and image was deleted
"""

import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.upgrade import (
    list_blueprint_images,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_image(client_factory, image_name=None, image_id=None):
    """Return the first image matching *image_id* or *image_name*, or None."""
    images = list_blueprint_images(client_factory)
    for img in images:
        if image_id and (img.get("id") == image_id):
            return img
        if image_name and (
            img.get("image_name") == image_name
            or img.get("filename") == image_name
            or img.get("label") == image_name
        ):
            return img
    return None


def _delete_image(client_factory, image_id):
    """DELETE /device-os/images/{image_id}."""
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/device-os/images/{image_id}", method="DELETE")
    if resp.status_code not in (200, 202, 204):
        raise RuntimeError(
            f"DELETE /device-os/images/{image_id} failed: "
            f"HTTP {resp.status_code} — {resp.text}"
        )


def _upload_image(client_factory, image_path, description, platform, image_type):
    """POST /device-os/images (multipart) and return the created image dict."""
    base = client_factory.get_base_client()
    file_name = os.path.basename(image_path)
    metadata = {}
    if description:
        metadata["description"] = description
    if platform:
        metadata["platform"] = platform
    if image_type:
        metadata["type"] = image_type

    with open(image_path, "rb") as fh:
        # The SDK's device_os.images.create() builds the multipart request.
        created = base.device_os.images.create(
            data=metadata,
            file_name=file_name,
            file_content=fh,
        )
    return created


# ---------------------------------------------------------------------------
# State handlers
# ---------------------------------------------------------------------------


def _handle_gathered(module, client_factory):
    images = list_blueprint_images(client_factory)
    return dict(
        changed=False,
        msg=f"{len(images)} image(s) found.",
        images=images,
    )


def _handle_present(module, client_factory):
    """Upload image if not already present (idempotent by image_name)."""
    id_param = module.params.get("id") or {}
    body = module.params.get("body") or {}

    image_path = body.get("image_path")
    if not image_path:
        module.fail_json(msg="'body.image_path' is required for state=present.")

    # Derive image name from the file name so callers don't have to specify id
    image_name_from_path = os.path.basename(image_path)
    image_name = id_param.get("image_name") or image_name_from_path
    image_id = id_param.get("image_id")

    description = body.get("description", "")
    platform = body.get("platform", "")
    image_type = body.get("image_type", "full")

    # Idempotency: check if the image already exists
    existing = _find_image(client_factory, image_name=image_name, image_id=image_id)
    if existing:
        return dict(
            changed=False,
            msg=f"Image '{image_name}' already exists (id={existing.get('id')}).",
            image=existing,
        )

    if module.check_mode:
        return dict(
            changed=True,
            msg=f"Would upload '{image_name}' from '{image_path}' (check mode — no action taken).",
        )

    if not os.path.isfile(image_path):
        module.fail_json(
            msg=f"Image file not found: {image_path}"
        )

    created = _upload_image(client_factory, image_path, description, platform, image_type)
    return dict(
        changed=True,
        msg=f"Image '{image_name}' uploaded successfully.",
        image=created,
    )


def _handle_absent(module, client_factory):
    """Delete image by name or UUID if it exists."""
    id_param = module.params.get("id") or {}
    image_name = id_param.get("image_name")
    image_id = id_param.get("image_id")

    if not image_name and not image_id:
        module.fail_json(
            msg="state=absent requires 'id.image_name' or 'id.image_id'."
        )

    existing = _find_image(client_factory, image_name=image_name, image_id=image_id)
    if not existing:
        ref = image_id or image_name
        return dict(
            changed=False,
            msg=f"Image '{ref}' not found — nothing to delete.",
        )

    resolved_id = existing.get("id")

    if module.check_mode:
        return dict(
            changed=True,
            msg=f"Would delete image '{resolved_id}' (check mode — no action taken).",
            image_id=resolved_id,
        )

    _delete_image(client_factory, resolved_id)
    return dict(
        changed=True,
        msg=f"Image '{resolved_id}' deleted.",
        image_id=resolved_id,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=True,
            choices=["present", "absent", "gathered"],
        ),
    )
    module_args = apstra_client_module_args() | object_module_args

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    result = dict(changed=False)

    try:
        client_factory = ApstraClientFactory.from_params(module)
        state = module.params["state"]

        if state == "gathered":
            result = _handle_gathered(module, client_factory)
        elif state == "present":
            result = _handle_present(module, client_factory)
        elif state == "absent":
            result = _handle_absent(module, client_factory)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
