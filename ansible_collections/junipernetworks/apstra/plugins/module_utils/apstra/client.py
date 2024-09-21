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
from aos.sdk.graph import Graph
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


def _add_resources_to_db(resources_db, full_resource_type, resources):
    """
    Helper method to add resources to the resource_db.

    Args:
        resource_db (dict): The database to store resources.
        full_resource_type (str): The type of the resource.
        resources (dict or list): The resources to add.
    """
    if full_resource_type not in resources_db:
        resources_db[full_resource_type] = {}
    if isinstance(resources, Graph):
        resources_db[full_resource_type][resources.id] = resources.compact_json()
    elif isinstance(resources, dict):
        if resources.get("id") is not None:
            # Individual resource
            resources_db[full_resource_type][resources["id"]] = resources
        elif resources.get("items", None) is not None:
            # Dictionary of list of resources
            for resource in resources["items"]:
                resource_id = resource.get("id")
                if resource_id is not None:
                    resources_db[full_resource_type][resource_id] = resource
        else:
            for resource in resources.values():
                if isinstance(resource, dict):
                    resource_id = resource.get("id")
                    if resource.get("id") is not None:
                        # Dictionary indexed by id
                        resources_db[full_resource_type][resource_id] = resources
                    else:
                        # Some leaf resources don't have an id, no need to add to db
                        break
    else:
        iterable = resources if isinstance(resources, list) else [resources]
        for resource in iterable:
            if resource.get("id") is not None:
                resources_db[full_resource_type][resource["id"]] = resource
            
def _add_parents_to_db(parents_db, parent, children):
    """
    Helper method to add resources to the resource_db.

    Args:
        parents_db (dict): The database of parents.
        parent (dict): The parent object of the children.
        children (iterable): List of children to add 
        parents for.
    """
    iterable = []
    if isinstance(children, dict):
        child_id = children.get("id")
        if child_id is not None:
            # Individual child
            iterable = [children]
        else:
            items = children.get("items")
            if items is not None:
                iterable = items
            else:
                # Something weird.
                # Likely a leaf resource
                return
    elif isinstance(children, list):
        iterable = children
    else:
        raise Exception(f"Invalid children type {children}")
    
    for child in iterable:
        child_id = child.get("id", None)
        if child_id is None:
            # some leaf resources don't have an id
            break
        
        parent_val = parents_db.get(child_id)
        if parent_val is None:
            parents_db[child_id] = parent
        else:
            raise Exception(f"Parent {parent_val['id']} already set for child {child['id']}")

# Gets the parent ids from parent_db for a resource
# identified by (plural) type and id. Ids of all parents
# are returned in the id dictionary.
# parents_db is a dictionary of child_id to parent_id
# resource_attrs is a list of resource types, from the 
# root type to the last type in the id.
def _get_parent_id(parents_db, resource_attrs, id):
    # Walk backwards through the resource types
    for i in range (len(resource_attrs) - 1, -1, -1):
        parent_attr = resource_attrs[i]
        if parent_attr in id:
            # Already have the parent id
            continue
        child_attr = resource_attrs[i + 1]
        child_id = id[child_attr]
        parent = parents_db.get(child_id)
        if parent is None:
            raise Exception(f"Parent not found for {child_id}")
        parent_id = parent.get("id", None)
        if parent_id is None:
            raise Exception(f"Parent {parent} has no id")
        id[parent_attr] = parent_id

# Map from plural to singular resource types
_plural_to_singular = [("ies","y"), ("s","")]

def singular_leaf_resource_type(resource_type):
    # Get the singular form of the leaf resource type
    # This is used for the id in the resource
    attrs = resource_type.split(".")
    return singular_resource_type(attrs[-1])

def singular_to_plural_id(id):
    # Get the plural form of the id
    # This is used for the id in the resource
    new_id = {}
    for key, value in id.items():
        new_id[plural_resource_type(key)] = value
    return new_id

def plural_to_singular_id(id):
    # Get the singular form of the id
    # This is used for the id in the resource
    new_id = {}
    for key, value in id.items():
        new_id[singular_resource_type(key)] = value
    return new_id

def singular_resource_type(resource_type):
    # Get the singular form of the resource type
    # This is used for the id in the resource
    for plural, singular in _plural_to_singular:
        if resource_type.endswith(plural):
            plural_type = resource_type[: -len(plural)] + singular
            return plural_type
    return resource_type

def plural_resource_type(resource_type):
    # Get the plural form of the resource type
    # This is used for the id in the resource
    for plural, singular in _plural_to_singular:
        if singular == "" and resource_type:
            singular_type = resource_type + plural
            return singular_type
        if resource_type.endswith(singular):
            singular_type = resource_type[: -len(singular)] + plural
            return singular_type
    return resource_type

# Get blueprint lock tag name
def _blueprint_lock_tag_name(blueprint_id):
    return "blueprint {} locked".format(blueprint_id)

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
        self._client_types = {
            "base_client": Client,
            "l3clos_client": l3closClient,
            "freeform_client": freeformClient,
            "endpointpolicy_client": endpointPolicyClient,
            "tags_client": tagsClient,
        }

        # Map client to types. Dotted types are traversed.
        # Should be in topological order (e.g.-- blueprints before blueprints.config_templates)
        self._client_to_types = {
            "l3clos_client": [
                "blueprints",
                "blueprints.virtual_networks",
                "blueprints.security_zones",
                "blueprints.routing_policies",
            ],
            "endpointpolicy_client": [
                "blueprints.endpoint_policies",
                "blueprints.endpoint_policies.application_points",
            ],
            "tags_client": ["blueprints.tags"],
        }

        # Populate the list (and set) of supported objects
        self.network_resources = []
        self.network_resources_set = {}
        for resource_client, resource_types in self._client_to_types.items():
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
        client_type = self._client_types.get(client_attr)
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

    def validate_id(self, resource_type, id):
        # Traverse nested resource_type
        attrs = resource_type.split(".")
        missing = []
        for attr in attrs:
            singular_attr = singular_resource_type(attr)
            if singular_attr not in id:
                missing.append(singular_attr)
        return missing

    # Call resource op. If op is 'get', will get one resource, or all resources of that type.
    # The id is a dictionary including any required keys for the resource type.
    # For example, for blueprints.virtual_networks, the id would be {'blueprint': 'my_blueprint', 'virtual_network': 'my_vn'}
    # If the leaf resource (e.g.- virtual_network) is not specified, all resources are returned (e.g. -- all virtual networks for a blueprint)
    def resources_op(self, resource_type, op="get", id={}, data=None):
        plural_id = singular_to_plural_id(id)
        return self._resources_op(resource_type, op, plural_id, data)

    # Internal method uses the plural types to simplify logic
    def _resources_op(self, resource_type, op="get", id={}, data=None):
        client = self.get_client(resource_type)

        # Traverse nested resource_type, using attrs to walk to object hierarchy
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
            if attr in id:
                # Get the id value
                id_value = id[attr]
                # Get the object
                obj = resource[id_value]
            elif leaf_type:
                obj = resource
            else:
                singular_attr = singular_resource_type(attr)
                raise Exception(
                    f"Missing required id attribute '{singular_attr}' for resource type '{resource_type}'"
                )

            # Nothing else to do if this is not the leaf type
            if not leaf_type:
                continue

            op_attr = None
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
    # Method used by Ansible module uses singular resource types, internally we use plural.
    def list_all_resources(self, resource_types, resource_id={}):
        plural_resource_id = singular_to_plural_id(resource_id)
        return self._list_all_resources(resource_types, plural_resource_id)

    # List all resources in the set of types and return them as a dictionary
    # resource_id types should be plural.
    def _list_all_resources(self, resource_types, resource_id={}):
        # sort the resource types in alphabetical order (also topological order)
        resource_types.sort()

        # Maintain a database of (root) resources. resource_db[root_type][id] can retrieve 
        # any root resource by ID. This is used to traverse the resource hierarchy.
        resources_db = {}

        # Maintain a dictionary of GUIDs to parent resource objects.
        # parents_db[child_id] can access the parent resource of any child_id.
        parents_db = {}

        # For each resource_type, get all the resources.
        # Use the id like a "cursor" to get the resources.

        for resource_type in resource_types:
            resource_attrs = resource_type.split(".")

            # Get the objects from the resource_db for this type
            root_type = resource_attrs[0]
            r_map = resources_db.get(root_type, {})
            if not r_map:
                resources_db[root_type] = r_map
                root_resources = self._resources_op(
                    root_type, "list", {}
                )
                # Only add the resource we care about
                # If we get by ID, we'll get a graph object.
                # Not what we want.
                if root_type in resource_id:
                    for root_resource in root_resources:
                        if root_resource["id"] == resource_id[root_type]:
                            _add_resources_to_db(
                                resources_db, root_type, root_resource
                            )
                            break
                else:
                    _add_resources_to_db(
                        resources_db, root_type, root_resources
                    )

            # Iterate through parent resources to get these resource
            for i in range(0, len(resource_attrs) - 1):
                parent_attr = resource_attrs[i]
                child_attr = resource_attrs[i + 1]

                # See if we have limited the id to a specific parent resource
                parent_full_resource_type = ".".join(resource_attrs[: i + 1])
                child_full_resource_type = ".".join(resource_attrs[: i + 2])

                # accumalate id's for the resource we're getting
                id = resource_id.copy() if resource_id else {}
                
                parent_db = resources_db.get(parent_full_resource_type, {})
                if not parent_db:
                    resources_db[parent_full_resource_type] = parent_db
                    parent_resources = self._resources_op(
                        parent_full_resource_type, "list", id
                    )
                    _add_resources_to_db(
                        resources_db, parent_full_resource_type, parent_resources
                    )
                    parent_db = resources_db[parent_full_resource_type]

                # Iterate through the ids of the parent resource to make sure we got it.
                for key in parent_db.keys():
                    id[parent_attr] = key
                    _get_parent_id(parents_db, resource_attrs[:i+1], id)
                    parent_value = resources_db[parent_full_resource_type][key]
                    if parent_value.get(child_attr) is None:
                        children = self._resources_op(
                            child_full_resource_type, "list", id
                        )
                        parent_value[child_attr] = children
                        _add_resources_to_db(
                            resources_db,
                            child_full_resource_type,
                            parent_value[child_attr],
                        )
                        _add_parents_to_db(parents_db, parent_value, children)

        return resources_db.get("blueprints", {})

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
                        "label": _blueprint_lock_tag_name(id),
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
        tag_name = _blueprint_lock_tag_name(id)

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
        tag = tags_client.blueprints[id].tags.get(label=_blueprint_lock_tag_name(id))
        return tag is not None

    # Commit the blueprint
    def commit_blueprint(self, id, timeout=DEFAULT_BLUEPRINT_COMMIT_TIMEOUT):
        blueprint_client = self.get_client("blueprints")
        start_time = time.time()
        interval = 5
        blueprint = None
        while blueprint == None:
            blueprint = blueprint_client.blueprints[id].get()
            if time.time() - start_time > timeout:
                raise Exception(
                    f"Failed to commit blueprint {id} within {timeout} seconds"
                )
            time.sleep(interval)
        return blueprint.commit()
