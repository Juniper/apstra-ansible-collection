from aos.sdk.client import (
    Client,
    ClientError,
)
from aos.sdk.reference_design.two_stage_l3clos import Client as l3closClient
from aos.sdk.reference_design.freeform.client import Client as freeformClient
from aos.sdk.reference_design.extension.endpoint_policy import (
    Client as endpointPolicyClient,
)
from aos.sdk.reference_design.extension.tags.client import Client as tagsClient
import os
import re
import time
from datetime import datetime

import urllib3

# Disable warnings about unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_BLUEPRINT_LOCK_TIMEOUT = 60
DEFAULT_BLUEPRINT_COMMIT_TIMEOUT = 120


def apstra_client_module_args():
    return dict(
        api_url=dict(type="str", required=False, default=os.getenv("APSTRA_API_URL")),
        verify_certificates=dict(
            type="bool",
            required=False,
            default=not (
                os.getenv("APSTRA_VERIFY_CERTIFICATES")
                in ["0", "false", "False", "FALSE", "no", "No", "NO"]
            ),
        ),
        auth_token=dict(
            type="str",
            required=False,
            no_log=True,
            default=os.getenv("APSTRA_AUTH_TOKEN"),
        ),
        username=dict(type="str", required=False, default=os.getenv("APSTRA_USERNAME")),
        password=dict(
            type="str",
            required=False,
            no_log=True,
            default=os.getenv("APSTRA_PASSWORD"),
        ),
        logout=dict(type="bool", required=False),
    )


class ApstraClientFactory:
    def __init__(
        self, api_url, verify_certificates, auth_token, username, password, logout
    ):
        self.api_url = api_url
        self.verify_certificates = verify_certificates
        self.auth_token = auth_token
        self.username = username
        self.password = password
        self.logout = logout
        self.user_id = None
        self.base_client = None
        self.l3clos_client = None
        self.freeform_client = None
        self.endpointpolicy_client = None
        self.tags_client = None

        # Map client members to client types
        self.client_types = {
            "base_client": Client,
            "l3clos_client": l3closClient,
            "freeform_client": freeformClient,
            "endpointpolicy_client": endpointPolicyClient,
            "tags_client": tagsClient,
        }

        # Map client to types. Dotted types are traversed.
        # Should be in topological order (e.g.-- blueprints before blueprints.config_templates)
        self.client_to_types = {
            "base_client": ["blueprints"],
            "freeform_client": ["blueprints.config_templates"],
            "l3clos_client": [
                "blueprints.virtual_networks",
                "blueprints.routing_zone_constraints",
            ],
            "endpointpolicy_client": [
                "blueprints.endpoint_policies",
                "blueprints.obj_policy_application_points",
            ],
            "tags_client": ["blueprints.tags"],
        }

        # Map from plural to singular resource types
        self.plural_to_singular = {"ies": "y", "es": "e", "s": ""}
        self.singular_to_plural = {
            plural: singular for singular, plural in self.plural_to_singular.items()
        }

        # Populate the list (and set) of supported objects
        self.network_resources = []
        self.network_resources_set = {}
        for resource_client, resource_types in self.client_to_types.items():
            for resource_type in resource_types:
                self.network_resources.append(resource_type)
                # Map the resource type to the client
                self.network_resources_set[resource_type] = resource_client

    @classmethod
    def from_params(cls, params):
        api_url = params.get("api_url")
        verify_certificates = params.get("verify_certificates")
        auth_token = params.get("auth_token")
        username = params.get("username")
        password = params.get("password")

        # Do not log out if auth_token is already set
        logout = params.get("logout")
        if logout is None:
            logout = not bool(auth_token)

        return cls(api_url, verify_certificates, auth_token, username, password, logout)

    def __del__(self):
        if self.logout:
            base_client = self.get_base_client()
            base_client.logout()

    def _login(self, client):
        if bool(self.auth_token):
            client.set_auth_token(self.auth_token)
        elif self.username and self.password:
            self.auth_token, self.user_id = client.login(self.username, self.password)
        else:
            raise Exception(
                "Missing required parameters: api_url, auth_token or (username and password)"
            )

    def _get_client(self, client_attr, client_class):
        client_instance = getattr(self, client_attr)
        if client_instance is None:
            client_instance = client_class(self.api_url, self.verify_certificates)
            setattr(self, client_attr, client_instance)
        self._login(client_instance)
        return client_instance

    def get_client(self, resource_type):
        client_attr = self.network_resources_set.get(resource_type)
        if client_attr is None:
            raise Exception("Unsupported resource type: {}".format(resource_type))
        client_type = self.client_types.get(client_attr)
        if client_type is None:
            raise Exception("Unsupported client type: {}".format(client_attr))
        return self._get_client(client_attr, client_type)

    def get_base_client(self):
        return self._get_client("base_client", Client)

    def get_l3clos_client(self):
        return self._get_client("l3clos_client", l3closClient)

    def get_freeform_client(self):
        return self._get_client("freeform_client", freeformClient)

    def get_endpointpolicy_client(self):
        return self._get_client("endpointpolicy_client", endpointPolicyClient)

    def get_tags_client(self):
        return self._get_client("tags_client", tagsClient)
    
    def singular_resource_type(self, resource_type):
        # Get the singular form of the resource type
        # This is used for the id in the resource
        for plural, singular in self.plural_to_singular.items():
            if resource_type.endswith(plural):
                return resource_type[: -len(plural)] + singular
        return resource_type

    def singular_leaf_resource_type(self, resource_type):
        # Get the singular form of the leaf resource type
        # This is used for the id in the resource
        attrs = resource_type.split(".")
        return self.singular_resource_type(attrs[-1])

    def plural_resource_type(self, resource_type):
        # Get the plural form of the resource type
        # This is used for the id in the resource
        for singular, plural in self.singular_to_plural.items():
            if resource_type.endswith(singular):
                return resource_type[: -len(singular)] + plural
        return resource_type

    def validate_id(self, resource_type, id):
        # Traverse nested resource_type
        attrs = resource_type.split(".")
        missing = []
        for attr in attrs:
            singular_attr = self.singular_resource_type(attr)
            if singular_attr not in id:
                missing.append(singular_attr)
        return missing 

    # Call operatop op. If op is 'get', will get one resource, or all resources of that type.
    # The id is a dictionary including any required keys for the resource type.
    # For example, for blueprints.virtual_networks, the id would be {'blueprint': 'my_blueprint', 'virtual_network': 'my_vn'}
    # If the leaf resource (e.g.- virtual_network) is not specified, all resources are returned (e.g. -- all virtual networks for a blueprint)
    def resources_op(self, resource_type, op="get", id={}, data=None):
        client = self.get_client(resource_type)

        # Traverse nested resource_type
        attrs = resource_type.split(".")
        obj = client
        for index, attr in enumerate(attrs):
            resource = getattr(obj, attr, None)
            if resource is None:
                raise Exception(
                    f"Resource type '{resource_type}' not defined for client {type(client).__name__}"
                )

            # Check if this is the leaf type
            leaf_type = index + 1 == len(attrs)

            # Iterate to the next object
            id_value = None
            singular_attr = self.singular_resource_type(attr)
            if singular_attr in id:
                # Get the id value
                id_value = id[singular_attr]
                # Get the object
                obj = resource[id_value]
            elif leaf_type:
                obj = resource
            else:
                raise Exception(
                    f"Missing required id attribute '{singular_attr}' for resource type '{resource_type}'"
                )

            # Nothing else to do if this is not the leaf type
            if not leaf_type:
                continue

            op_attr = None

            if id_value is None:
                # Try list then get if id is not specified
                if op in ["list", "get"]:
                    try:
                        op_attr = getattr(obj, "list")
                    except AttributeError:
                        try:
                            op_attr = getattr(obj, "get")
                        except AttributeError:
                            raise Exception(
                                f"Operation 'list' and 'get' not defined for resource type '{resource_type}'"
                            )
                else:
                    try:
                        # Could be a create operation
                        op_attr = getattr(obj, op)
                    except AttributeError:
                        raise Exception(
                            f"Invalid operation '{op}' for resource type '{resource_type}', id '{id}'"
                        )

            if op_attr is None:
                op_attr = getattr(obj, op)
                if op_attr is None:
                    raise Exception(
                        f"Operation '{op}' not defined for resource type '{resource_type}'"
                    )

            # Call the op on the object
            try:
                if data is None:
                    return op_attr()
                else:
                    return op_attr(data)
            except TypeError as te:
                # Bug -- 404 results in None, which generated API blindly subscripts
                if te.args[0] == "'NoneType' object is not subscriptable":
                    return None

    # List all resources in the set of types and return them as a dictionary
    def list_all_resources(self, resource_types):
        # sort the resource types in alphabetical order (also topological order)
        resource_types.sort()

        # accumulate the resources in a map
        resources_map = {}

        for resource_type in resource_types:
            resource_attrs = resource_type.split(".")

            # accumalate id's for the resource we're getting
            id = {}
            r_map = resources_map

            # build the context required for the nested resource
            for index, resource_attr in enumerate(resource_attrs):
                # Get the full type of the parent resource.
                full_resource_type = ".".join(resource_attrs[: index + 1])

                # Make sure we got the parent resource
                if not resource_attr in r_map:
                    r_map[resource_attr] = self.resources_op(
                        full_resource_type, "list", id
                    )

                leaf_type = index + 1 == len(resource_attrs)
                if leaf_type:
                    # Done with this resource_type
                    break

                # Get the type of the next resource
                next_resource_attr = resource_attrs[index + 1]
                next_full_resource_type = ".".join(resource_attrs[: index + 2])

                # Need to loop through all instances of this resource to get child resources
                resources = r_map[resource_attr]
                if isinstance(resources, dict) and hasattr(resources, "id"):
                    # Single resource, get the id and get the child resources
                    singular_resource_attr = self.singular_resource_type(
                        resource_attr
                    )
                    id[singular_resource_attr] = resources["id"]
                    r_map = resources
                    r_map[next_resource_attr] = self.resources_op(
                        next_full_resource_type, "list", id
                    )
                elif isinstance(resources, (list, dict)):
                    # Treat a list or dictionary of resources the same way
                    iterable = (
                        resources if isinstance(resources, list) else resources.values()
                    )
                    for resource in iterable:
                        singular_resource_attr = self.singular_resource_type(
                            resource_attr
                        )
                        id[singular_resource_attr] = resource["id"]
                        r_map = resource
                        r_map[next_resource_attr] = self.resources_op(
                            next_full_resource_type, "list", id
                        )
                elif resources is None:
                    # No resources found, nothing to do
                    break
                else:
                    raise Exception(
                        f"Internal error: invalid data in resource map for {resource_attr}: {resources}"
                    )
        return resources_map

    # Get blueprint lock tag name
    def _blueprint_lock_tag_name(self, blueprint_id):
        return "blueprint {} locked".format(blueprint_id)

    def lock_blueprint(self, id, timeout=DEFAULT_BLUEPRINT_LOCK_TIMEOUT):
        tags_client = self.get_tags_client()
        start_time = time.time()
        interval = 5
        locked_pattern = (
            r"(Tag with label '(.+)' already exists|Blueprint is still being created)"
        )

        while True:
            try:
                tags_client.blueprints[id].tags.create(
                    data={
                        "label": self._blueprint_lock_tag_name(id),
                        "description": "blueprint locked at {}".format(
                            datetime.now().isoformat()
                        ),
                    }
                )
                break  # Exit the loop if the lock is successful
            except ClientError as ce:
                error_message = str(ce)
                if re.search(locked_pattern, error_message):
                    if time.time() - start_time > timeout:
                        raise Exception(
                            f"Failed to lock blueprint {id} within {timeout} seconds: {ce}"
                        )
                    time.sleep(interval)
                else:
                    raise Exception(
                        f"Unexpected ClientError trying to lock blueprint {id} within {timeout} seconds: {ce}"
                    )
            except Exception as e:
                raise Exception(
                    f"Unexpected Exception trying to lock blueprint {id} within {timeout} seconds: {e}"
                )

    # Unlock the blueprint
    def unlock_blueprint(self, id):
        tags_client = self.get_tags_client()
        tag_name = self._blueprint_lock_tag_name(id)

        # Need to get look through all the tags
        tags = tags_client.blueprints[id].tags.list()
        for tag in tags:
            if tag["label"] == tag_name:
                tags_client.blueprints[id].tags[tag["id"]].delete()
                return

        # Tag was not locked. This is exceptional.
        raise Exception(f"Blueprint {id} is not locked")

    # Ensure that the blueprint is locked
    def check_blueprint_locked(self, id):
        # Try to get the tag on the given blueprint
        tags_client = self.get_tags_client()
        tag = tags_client.blueprints[id].tags.get(
            label=self._blueprint_lock_tag_name(id)
        )
        return tag is not None

    # Commit the blueprint
    def commit_blueprint(self, id, timeout=DEFAULT_BLUEPRINT_COMMIT_TIMEOUT):
        base_client = self.get_base_client()
        start_time = time.time()
        interval = 5
        blueprint = None
        while blueprint == None:
            blueprint = base_client.blueprints[id].get()
            if time.time() - start_time > timeout:
                raise Exception(f"Failed to commit blueprint {id} within {timeout} seconds")
            time.sleep(interval)
        return blueprint.commit()