from aos.sdk.client import (
    Client,
    ClientError,
)
from aos.sdk.reference_design.two_stage_l3clos import Client as l3closClient
from aos.sdk.reference_design.freeform.client import Client as freeformClient
from aos.sdk.reference_design.extension.endpoint_policy import (
    Client as endpointPolicyClient,
)
from aos.sdk.reference_design.extension.resource_allocation import (
    Client as resourceAllocationClient,
)
from aos.sdk.reference_design.extension.tags.client import Client as tagsClient
from aos.sdk.graph import Graph
import os
import re
import time
from datetime import datetime
from ansible.module_utils.basic import AnsibleModule

import urllib3

# Disable warnings about unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_BLUEPRINT_LOCK_TIMEOUT = 60
DEFAULT_BLUEPRINT_COMMIT_TIMEOUT = 120


def apstra_client_module_args():
    """
    Return the module arguments for an Apstra module.

    :return: The module arguments.
    """
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
        logout=dict(type="bool", required=False, default=False),
    )


def _add_objects_to_db(objects_db, full_object_type, objects):
    """
    Helper method to add objects to the object_db.

    Args:
        object_db (dict): The database to store objects.
        full_object_type (str): The type of the object.
        objects (dict or list): The objects to add.
    """
    if full_object_type not in objects_db:
        objects_db[full_object_type] = {}
    if isinstance(objects, Graph):
        objects_db[full_object_type][objects.id] = objects.compact_json()
    elif isinstance(objects, dict):
        if objects.get("id") is not None:
            # Individual object
            objects_db[full_object_type][objects["id"]] = objects
        elif objects.get("items", None) is not None:
            # Dictionary of list of objects
            for object in objects["items"]:
                object_id = object.get("id")
                if object_id is not None:
                    objects_db[full_object_type][object_id] = object
        else:
            for object in objects.values():
                if isinstance(object, dict):
                    object_id = object.get("id")
                    if object.get("id") is not None:
                        # Dictionary indexed by id
                        objects_db[full_object_type][object_id] = objects
                    else:
                        # Some leaf objects don't have an id, no need to add to db
                        break
    else:
        iterable = objects if isinstance(objects, list) else [objects]
        for object in iterable:
            if object.get("id") is not None:
                objects_db[full_object_type][object["id"]] = object


def _add_parents_to_db(parents_db, parent, children):
    """
    Helper method to add objects to the object_db.

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
                # Likely a leaf object
                return
    elif isinstance(children, list):
        iterable = children
    else:
        raise Exception(f"Invalid children type {children}")

    for child in iterable:
        child_id = child.get("id", None)
        if child_id is None:
            # some leaf objects don't have an id
            break

        parent_val = parents_db.get(child_id)
        if parent_val is None:
            parents_db[child_id] = parent
        else:
            # Nothing to do if the parent is already set
            return


def _get_parent_id(parents_db, object_attrs, id):
    """
    Get the parent ids from the parent_db for an object identified by (plural) type and id.
    Ids of all parents are returned in the id dictionary.
    
    :param parents_db: A dictionary of child_id to parent_id.
    :param object_attrs: A list of object types, from the root type to the last type in the id.
    :param id: The dictionary of ids.
    
    :raises Exception: If the parent is not found or has no id.
    """
    # Walk backwards through the object types
    for i in range(len(object_attrs) - 1, -1, -1):
        parent_attr = object_attrs[i]
        if parent_attr in id:
            # Already have the parent id
            continue
        child_attr = object_attrs[i + 1]
        child_id = id[child_attr]
        parent = parents_db.get(child_id)
        if parent is None:
            raise Exception(f"Parent not found for {child_id}")
        parent_id = parent.get("id", None)
        if parent_id is None:
            raise Exception(f"Parent {parent} has no id")
        id[parent_attr] = parent_id


# Map from plural to singular object types
_plural_to_singular = [("ies", "y"), ("s", "")]


def singular_leaf_object_type(object_type):
    """
    Get the singular form of the leaf object type.
    
    :param object_type: The object type.
    """
    attrs = object_type.split(".")
    return singular_object_type(attrs[-1])


def singular_to_plural_id(id):
    """
    Get the plural form of the id.
    
    :param id: The id dictionary.
    :return: The id dictionary with plural object types.
    """
    new_id = {}
    for key, value in id.items():
        new_id[plural_object_type(key)] = value
    return new_id


def plural_to_singular_id(id):
    """
    Get the singular form of the id.
    
    :param id: The id dictionary.
    :return: The id dictionary with singular object types.
    """
    new_id = {}
    for key, value in id.items():
        new_id[singular_object_type(key)] = value
    return new_id


def singular_object_type(object_type):
    """
    Get the singular form of the object type.
    
    :param object_type: The object type.
    :return: The singular form of the object type.
    """
    for plural, singular in _plural_to_singular:
        if object_type.endswith(plural):
            plural_type = object_type[: -len(plural)] + singular
            return plural_type
    return object_type


def plural_object_type(object_type):
    """
    Get the plural form of the object type.
    
    :param object_type: The object type.
    :return: The plural form of the object type.
    """
    for plural, singular in _plural_to_singular:
        if singular == "" and object_type:
            singular_type = object_type + plural
            return singular_type
        if object_type.endswith(singular):
            singular_type = object_type[: -len(singular)] + plural
            return singular_type
    return object_type


def _blueprint_lock_tag_name(blueprint_id):
    """
    Get the tag name for locking a blueprint.
    
    :param blueprint_id: The ID of the blueprint.
    :return: The tag name.
    """
    return "blueprint {} locked".format(blueprint_id)


class ApstraClientFactory:
    """
    Factory class to create and manage Apstra clients.
    
    :param module: The Ansible module.
    :param api_url: The URL of the AOS API.
    :param verify_certificates: Whether to verify SSL certificates.
    :param auth_token: The authentication token.
    :param username: The username for authentication.
    :param password: The password for authentication.
    :param logout: Whether to log out after the operation.
    """
    def __init__(
        self,
        module,
        api_url,
        verify_certificates,
        auth_token,
        username,
        password,
        logout,
    ):
        self.module = module
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
        self.resource_allocation_client = None

        # Map client members to client types
        self._client_types = {
            "base_client": Client,
            "l3clos_client": l3closClient,
            "freeform_client": freeformClient,
            "endpointpolicy_client": endpointPolicyClient,
            "tags_client": tagsClient,
            "resource_allocation_client": resourceAllocationClient,
        }

        # Map client to types. Dotted types are traversed.
        # Should be in topological order (e.g.-- blueprints before blueprints.config_templates)
        self._client_to_types = {
            "base_client": [
                "asn_pools",
                "device_pools",
                "integer_pools",
                "ip_pools",
                "ipv6_pools",
                "vlan_pools",
                "vni_pools",
            ],
            "l3clos_client": [
                "blueprints",
                "blueprints.virtual_networks",
                "blueprints.security_zones",
                "blueprints.resource_groups",
                "blueprints.routing_policies",
                "blueprints.tags",
            ],
            "endpointpolicy_client": [
                "blueprints.policy_types",
                "blueprints.endpoint_policies",
                "blueprints.endpoint_policies.application_points",
            ],
            "tags_client": ["blueprints.tags"],
            "resource_allocation_client": ["blueprints.resource_groups"],
        }

        # Populate the list (and set) of supported objects
        self.network_objects = []
        self.network_objects_set = {}
        for object_client, object_types in self._client_to_types.items():
            for object_type in object_types:
                self.network_objects.append(object_type)
                # Map the object type to the client
                self.network_objects_set[object_type] = object_client

    @classmethod
    def from_params(cls, module):
        """
        Create an ApstraClientFactory from the module parameters.
        
        :param module: The Ansible module.
        """
        api_url = module.params.get("api_url")
        verify_certificates = module.params.get("verify_certificates")
        auth_token = module.params.get("auth_token")
        username = module.params.get("username")
        password = module.params.get("password")

        # Do not log out if auth_token is already set
        logout = module.params.get("logout")
        if logout is None:
            logout = not bool(auth_token)

        return cls(
            module=module,
            api_url=api_url,
            verify_certificates=verify_certificates,
            auth_token=auth_token,
            username=username,
            password=password,
            logout=logout,
        )

    def __del__(self):
        """
        Log out when the object is deleted.
        """
        if self.logout:
            base_client = self.get_base_client()
            base_client.logout()

    def _login(self, client):
        """
        Log in to the client.
        :param client: The client to log in to.
        """
        if bool(self.auth_token):
            client.set_auth_token(self.auth_token)
        elif self.username and self.password:
            self.auth_token, self.user_id = client.login(self.username, self.password)
        else:
            raise Exception(
                "Missing required parameters: api_url, auth_token or (username and password)"
            )

    def _get_client(self, client_attr, client_class):
        """
        Get the client instance for the given attribute.
        :param client_attr: The attribute name of the client.
        :param client_class: The class of the client.
        :return: The client instance.
        """
        client_instance = getattr(self, client_attr)
        if client_instance is None:
            client_instance = client_class(self.api_url, self.verify_certificates)
            setattr(self, client_attr, client_instance)
        self._login(client_instance)
        return client_instance

    def get_client(self, object_type):
        """
        Get the client for the given object type.
        :param object_type: The object type.
        :return: The client instance.
        """
        client_attr = self.network_objects_set.get(object_type)
        if client_attr is None:
            raise Exception("Unsupported object type: {}".format(object_type))
        client_type = self._client_types.get(client_attr)
        if client_type is None:
            raise Exception("Unsupported client type: {}".format(client_attr))
        return self._get_client(client_attr, client_type)

    def get_base_client(self):
        """
        Get the base client.
        :return: The base client instance.
        """
        return self._get_client("base_client", Client)

    def get_l3clos_client(self):
        """
        Get the L3 CLOS client.
        :return: The L3 CLOS client instance.
        """
        return self._get_client("l3clos_client", l3closClient)

    def get_freeform_client(self):
        """
        Get the freeform client.
        :return: The freeform client instance."""
        return self._get_client("freeform_client", freeformClient)

    def get_endpointpolicy_client(self):
        """
        Get the endpoint policy client.
        :return: The endpoint policy client instance.
        """
        return self._get_client("endpointpolicy_client", endpointPolicyClient)

    def get_tags_client(self):
        """
        Get the tags client.
        :return: The tags client instance.
        """
        return self._get_client("tags_client", tagsClient)

    def get_resource_allocation_client(self):
        """
        Get the resource allocation client.
        :return: The resource allocation client instance.
        """
        return self._get_client("resource_allocation_client", resourceAllocationClient)

    def validate_id(self, object_type, id):
        """
        Validate the id for the object type.
        :param object_type: The object type.
        :param id: The id dictionary.
        :return: A list of missing required attributes.
        """
        # Traverse nested object_type
        attrs = object_type.split(".")
        missing = []
        for attr in attrs:
            singular_attr = singular_object_type(attr)
            if singular_attr not in id:
                missing.append(singular_attr)
        return missing

    def object_request(self, object_type, op="get", id={}, data=None):
        """
        Call object op. If op is 'get', will get one object, or all objects of that type.
        If data is supplied, it will be passed into the operation on create or update.
        For "get" or "list" operations, the result can be filtered by label if the
        label key is found in the data dictionary.
        The id is a dictionary including any required keys for the object type.
        For example, for blueprints.virtual_networks, the id would be {'blueprint': 'my_blueprint', 'virtual_network': 'my_vn'}
        If the leaf object (e.g.- virtual_network) is not specified, all objects are returned (e.g. -- all virtual networks for a blueprint)

        :param object_type: The object type.
        :param op: The operation to perform.
        :param id: The id dictionary.
        :param data: The data to pass to the operation.
        :return: The result of the operation.
        """
        plural_id = singular_to_plural_id(id)
        return self._object_request(object_type, op, plural_id, data)

    def _object_request(self, object_type, op="get", id={}, data=None):
        """
        Call object op. If op is 'get', will get one object, or all objects of that type.
        Internal method uses the plural types to simplify logic
        
        :param object_type: The object type.
        :param op: The operation to perform.
        :param id: The id dictionary.
        :param data: The data to pass to the operation.
        :return: The result of the operation.
        """
        client = self.get_client(object_type)

        # Traverse nested object_type, using attrs to walk to object hierarchy
        attrs = object_type.split(".")
        obj = client
        label = None
        for index, attr in enumerate(attrs):
            object = getattr(obj, attr, None)
            if object is None:
                raise Exception(
                    f"Object type '{object_type}' not defined for client {type(client).__name__}"
                )

            # Check if this is the leaf type
            leaf_type = index + 1 == len(attrs)

            # Iterate to the next object
            id_value = None
            if attr in id:
                # Get the id value
                id_value = id[attr]
                # Get the object
                obj = object[id_value]
            elif leaf_type:
                obj = object
                label = data.get("label") if isinstance(data, dict) else None
            else:
                singular_attr = singular_object_type(attr)
                raise Exception(
                    f"Missing required id attribute '{singular_attr}' for object type '{object_type}'"
                )

            # Nothing else to do if this is not the leaf type
            if not leaf_type:
                continue

            op_attr = None
            read_only = op in ["list", "get"]
            no_arg = True if op in ["delete"] else read_only
            # Try list then get if id is not specified
            if read_only:
                try:
                    op_attr = getattr(obj, "list")
                except AttributeError:
                    try:
                        op_attr = getattr(obj, "get")
                    except AttributeError:
                        raise Exception(
                            f"Operation 'list' and 'get' not defined for object type '{object_type}'"
                        )
            else:
                try:
                    # Could be a create operation
                    op_attr = getattr(obj, op)
                except AttributeError:
                    raise Exception(
                        f"Invalid operation '{op}' for object type '{object_type}', id '{id}'"
                    )

            # Call the op on the object
            try:
                if no_arg:
                    ret = op_attr()
                    if read_only and label:
                        iterable = None
                        if isinstance(ret, list):
                            iterable = ret
                        elif isinstance(ret, dict):
                            if "id" in ret:
                                iterable = [ret]
                            elif "items" in ret:
                                iterable = ret["items"]
                            else:
                                iterable = ret.values()
                        # Filter the result by label
                        for object in iterable:
                            if object.get("label") == label:
                                return object
                        return None
                    else:
                        return ret
                else:
                    return op_attr(data)
            except TypeError as te:
                # Bug -- 404 results in None, which generated API blindly subscripts
                if te.args[0] == "'NoneType' object is not subscriptable":
                    return None

    # List all objects in the set of types and return them as a dictionary
    # Method used by Ansible module uses singular object types, internally we use plural.
    def list_all_objects(self, object_types, object_id={}):
        plural_object_id = singular_to_plural_id(object_id)
        return self._list_all_objects(object_types, plural_object_id)

    # List all objects in the set of types and return them as a dictionary
    # object_id types should be plural.
    def _list_all_objects(self, object_types, object_id={}):
        # sort the object types in alphabetical order (also topological order)
        object_types.sort()

        # Maintain a database of (root) objects. object_db[root_type][id] can retrieve
        # any root object by ID. This is used to traverse the object hierarchy.
        objects_db = {}

        # Maintain a dictionary of GUIDs to parent object objects.
        # parents_db[child_id] can access the parent object of any child_id.
        parents_db = {}

        # Map of all the root objects that are encountered.
        root_types = {}

        # For each object_type, get all the objects.
        # Use the id like a "cursor" to get the objects.

        for object_type in object_types:
            object_attrs = object_type.split(".")

            # Get the objects from the object_db for this type
            root_type = object_attrs[0]
            root_types[root_type] = {}
            r_map = objects_db.get(root_type, {})
            if not r_map:
                objects_db[root_type] = r_map
                root_objects = self._object_request(root_type, "list", {})
                # Only add the object we care about
                # If we get by ID, we'll get a graph object.
                # Not what we want.
                if root_type in object_id:
                    for root_object in root_objects:
                        if root_object["id"] == object_id[root_type]:
                            _add_objects_to_db(objects_db, root_type, root_object)
                            break
                else:
                    _add_objects_to_db(objects_db, root_type, root_objects)

            # Iterate through parent objects to get these object
            for i in range(0, len(object_attrs) - 1):
                parent_attr = object_attrs[i]
                child_attr = object_attrs[i + 1]

                # See if we have limited the id to a specific parent object
                parent_full_object_type = ".".join(object_attrs[: i + 1])
                child_full_object_type = ".".join(object_attrs[: i + 2])

                # accumalate id's for the object we're getting
                id = object_id.copy() if object_id else {}

                parent_db = objects_db.get(parent_full_object_type, {})
                if not parent_db:
                    objects_db[parent_full_object_type] = parent_db
                    parent_objects = self._object_request(
                        parent_full_object_type, "list", id
                    )
                    _add_objects_to_db(
                        objects_db, parent_full_object_type, parent_objects
                    )
                    parent_db = objects_db[parent_full_object_type]

                # Iterate through the ids of the parent object to make sure we got it.
                for key in parent_db.keys():
                    id[parent_attr] = key
                    _get_parent_id(parents_db, object_attrs[: i + 1], id)
                    parent_value = objects_db[parent_full_object_type][key]
                    if parent_value.get(child_attr) is None:
                        children = self._object_request(
                            child_full_object_type, "list", id
                        )
                        parent_value[child_attr] = children
                        _add_objects_to_db(
                            objects_db,
                            child_full_object_type,
                            parent_value[child_attr],
                        )
                        _add_parents_to_db(parents_db, parent_value, children)

        # Return all the objects by starting at the root type
        for root_type in root_types.keys():
            root_types[root_type] = objects_db.get(root_type, {})
        return root_types

    def lock_blueprint(self, id, timeout=DEFAULT_BLUEPRINT_LOCK_TIMEOUT):
        """
        Lock the blueprint with the given ID.
        This is a "gentlemen's agreement" lock, not a true lock.
        A tag is used for locking.
        
        :param id: The ID of the blueprint to lock.
        :param timeout: The maximum time to wait for the blueprint to be locked.
        :return: True if the blueprint was locked, False if not.
        """
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
                # Successfully locked
                return True
            except ClientError as ce:
                error_message = str(ce)
                if re.search(locked_pattern, error_message):
                    time_left = timeout - (time.time() - start_time)
                    if time_left <= 0:
                        self.module.fail_json(msg=f"Failed to lock blueprint {id} within {timeout} seconds")
                    self.module.debug(f"Blueprint {id} is locked, waiting up to {time_left} seconds for unlock...")
                    time.sleep(interval)
                else:
                    self.module.fail_json(msg=f"Unexpected ClientError trying to lock blueprint {id} within {timeout} seconds: {e}")
            except Exception as e:
                self.module.fail_json(msg=f"Unexpected Exception trying to lock blueprint {id} within {timeout} seconds: {e}")

    def unlock_blueprint(self, id):
        """
        Unlock the blueprint with the given ID.
        :param id: The ID of the blueprint to unlock.
        :return: True if the blueprint was unlocked, False if not.
        """
        tags_client = self.get_tags_client()
        tag_name = _blueprint_lock_tag_name(id)

        # Need to get look through all the tags
        tags = tags_client.blueprints[id].tags.list()
        for tag in tags:
            if tag["label"] == tag_name:
                tags_client.blueprints[id].tags[tag["id"]].delete()
                return True

        # Tag was not locked.
        return False

    def check_blueprint_locked(self, id):
        """
        Check if the blueprint with the given ID is locked.
        :param id: The ID of the blueprint to check.
        :return: True if the blueprint is locked, False if not.
        """
        # Try to get the tag on the given blueprint
        tags_client = self.get_tags_client()
        tag = tags_client.blueprints[id].tags.get(label=_blueprint_lock_tag_name(id))
        return tag is not None

    def commit_blueprint(self, id, timeout=DEFAULT_BLUEPRINT_COMMIT_TIMEOUT):
        """
        Commit the blueprint with the given ID.
        
        :param id: The ID of the blueprint to commit.
        :param timeout: The maximum time to wait for the blueprint to be committed.
        :return: True if the blueprint was committed, False if not.
        """
        blueprint_client = self.get_client("blueprints")
        start_time = time.time()
        interval = 5
        blueprint = None
        while blueprint == None:
            blueprint = blueprint_client.blueprints[id].get()
            time_left = timeout - (time.time() - start_time)
            if time_left <= 0:
                self.module.fail_json(msg=f"Failed to commit blueprint {id} within {timeout} seconds")
            self.module.debug(f"Waiting {time_left} seconds for blueprint to be committed...")
            time.sleep(interval)

        is_committed = blueprint.is_committed()
        if not is_committed:
            blueprint.commit()
        return not is_committed

    def compare_and_update(self, current, desired, changes):
        """
        Recursively compare and update the current state to match the desired state.
        
        :param current: The current state dictionary.
        :param desired: The desired state dictionary.
        :param changes: A dictionary to track changes.
        :return: True if any changes were made, False otherwise.
        """
        changed = False
        for key, desired_value in desired.items():
            if key not in current:
                # Field is missing in the current state, probably only for create
                self.module.debug(f"Field '{key}' missing in current state, ignoring it")
                continue
            
            current_value = current[key]
            
            if isinstance(desired_value, dict) and isinstance(current_value, dict):
                # Recursively compare nested dictionaries
                nested_changes = {}
                nested_changed = self.compare_and_update(current_value, desired_value, nested_changes)
                if nested_changed:
                    changes[key] = nested_changes
                    changed = True
            elif isinstance(desired_value, list) and isinstance(current_value, list):
                # Compare lists
                if current_value != desired_value:
                    current[key] = desired_value
                    changes[key] = desired_value
                    changed = True
            elif current_value != desired_value:
                # Update the current state and track the change
                current[key] = desired_value
                changes[key] = desired_value
                changed = True
        
        return changed

    def extract_field(self, data, field_name):
        """
        Extract a top-level field from a dictionary, remove it from the original dictionary,
        and return it in a new dictionary.

        :param data: The original dictionary.
        :param field_name: The field to extract.
        :return: A new dictionary containing the extracted field, or None.
        """
        if field_name not in data:
            # Nothing to do
            return None
        
        # Extract the field
        field_value = data.pop(field_name)
        
        # Return the field in a new dictionary
        return {field_name: field_value}

    def update_tags(self, id, leaf_type, tags):
        """
        Update the tags for a leaf object.

        :param id: The ID of the leaf object.
        :param leaf_type: The type of the leaf object.
        :param tags: The tags to set.
        """
        # Get the blueprint id from the id dict
        blueprint_id = id.get("blueprint")
        if blueprint_id is None:
            self.module.fail_json(msg="Missing 'blueprint' in id")

        # Get the set of tags for the blueprint
        tags_client = self.get_tags_client()
        all_tags = tags_client.blueprints[blueprint_id].tags.list()
        all_tags_set = {tag['label'] for tag in all_tags if 'label' in tag}
        
        # Create a set of requested tags for quick lookup
        tags_set = set(tags)

        # Make sure all requested tags are present
        if not all_tags_set.issuperset(tags_set):
            missing_tags = tags_set.difference(all_tags_set)
            self.module.fail_json(msg=f"update_tags failed: missing tags: {missing_tags}")

        # Find out what tags are not set
        missing_tags = all_tags_set.difference(tags_set)

        # Update the tags
        tags_client.blueprints[blueprint_id].tagging([id[leaf_type]], tags, list(missing_tags))
        self.module.debug(f"Tags updated for {leaf_type} {id}, ADDED: {tags}, REMOVED: {missing_tags}")
        return tags