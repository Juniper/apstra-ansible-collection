from aos.sdk.client import Client
from aos.sdk.reference_design.two_stage_l3clos import Client as l3closClient
from aos.sdk.reference_design.freeform.client import Client as freeformClient
from aos.sdk.reference_design.extension.endpoint_policy import (
    Client as endpointPolicyClient,
)
from aos.sdk.reference_design.extension.tags.client import Client as tagsClient
import os


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
            "base_client": ["blueprints", "blueprints.tasks"],
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

    # Call operatop op. If op is 'get', will get one resource, or all resources of that type.
    # The id is a dictionary including any required keys for the resource type.
    # For example, for blueprints.virtual_networks, the id would be {'blueprints': 'my_blueprint', 'virtual_networks': 'my_vn'}
    # If the leaf resource (e.g.- virtual_network) is not specified, all resources are returned (e.g. -- all virtual networks for a blueprint)
    def resources_op(self, resource_type, op, id={}):
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
            leaf_type = (index + 1 == len(attrs))

            # Iterate to the next object
            id_value = None
            if attr in id:
                # Get the id value
                id_value = id[attr]
                # Get the object
                obj = resource[id_value]
            elif leaf_type:
                obj = resource
            else:
                raise Exception(
                    f"Missing required id attribute '{attr}' for resource type '{resource_type}'"
                )

            # Nothing else to do if this is not the leaf type
            if not leaf_type:
                continue

            op_attr = None

            # If this is the leaf object, and the id is not specified, then this is a list operation
            if id_value is None:
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
                return op_attr()
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
                    r_map[resource_attr] = self.resources_op(full_resource_type, "list", id)

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
                    id[resource_attr] = resources["id"]
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
                        id[resource_attr] = resource["id"]
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
