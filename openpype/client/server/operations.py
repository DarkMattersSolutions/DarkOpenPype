import re
import copy
import json
import collections
import uuid
import datetime

from bson.objectid import ObjectId

from openpype.client.operations_base import (
    REMOVED_VALUE,
    CreateOperation,
    UpdateOperation,
    DeleteOperation,
    BaseOperationsSession
)

from openpype.client.mongo.operations import (
    CURRENT_THUMBNAIL_SCHEMA,
    CURRENT_REPRESENTATION_SCHEMA,
    CURRENT_HERO_VERSION_SCHEMA,
    CURRENT_VERSION_SCHEMA,
    CURRENT_SUBSET_SCHEMA,
    CURRENT_ASSET_DOC_SCHEMA,
    CURRENT_PROJECT_SCHEMA,
)

from .server_api import get_server_api_connection
from .conversion_utils import (
    convert_create_asset_to_v4,
    convert_create_task_to_v4,
    convert_create_subset_to_v4,
    convert_create_version_to_v4,
    convert_create_representation_to_v4,

    convert_update_subset_to_v4,
    convert_update_version_to_v4,
    convert_update_representation_to_v4,
)
from .utils import create_entity_id


PROJECT_NAME_ALLOWED_SYMBOLS = "a-zA-Z0-9_"
PROJECT_NAME_REGEX = re.compile(
    "^[{}]+$".format(PROJECT_NAME_ALLOWED_SYMBOLS)
)


def _create_or_convert_to_id(entity_id=None):
    if entity_id is None:
        return create_entity_id()

    if isinstance(entity_id, ObjectId):
        raise TypeError("Type of 'ObjectId' is not supported anymore.")

    # Validate if can be converted to uuid
    uuid.UUID(entity_id)
    return entity_id


def new_project_document(
    project_name, project_code, config, data=None, entity_id=None
):
    """Create skeleton data of project document.

    Args:
        project_name (str): Name of project. Used as identifier of a project.
        project_code (str): Shorter version of projet without spaces and
            special characters (in most of cases). Should be also considered
            as unique name across projects.
        config (Dic[str, Any]): Project config consist of roots, templates,
            applications and other project Anatomy related data.
        data (Dict[str, Any]): Project data with information about it's
            attributes (e.g. 'fps' etc.) or integration specific keys.
        entity_id (Union[str, ObjectId]): Predefined id of document. New id is
            created if not passed.

    Returns:
        Dict[str, Any]: Skeleton of project document.
    """

    if data is None:
        data = {}

    data["code"] = project_code

    return {
        "_id": _create_or_convert_to_id(entity_id),
        "name": project_name,
        "type": CURRENT_PROJECT_SCHEMA,
        "entity_data": data,
        "config": config
    }


def new_asset_document(
    name, project_id, parent_id, parents, data=None, entity_id=None
):
    """Create skeleton data of asset document.

    Args:
        name (str): Is considered as unique identifier of asset in project.
        project_id (Union[str, ObjectId]): Id of project doument.
        parent_id (Union[str, ObjectId]): Id of parent asset.
        parents (List[str]): List of parent assets names.
        data (Dict[str, Any]): Asset document data. Empty dictionary is used
            if not passed. Value of 'parent_id' is used to fill 'visualParent'.
        entity_id (Union[str, ObjectId]): Predefined id of document. New id is
            created if not passed.

    Returns:
        Dict[str, Any]: Skeleton of asset document.
    """

    if data is None:
        data = {}
    if parent_id is not None:
        parent_id = _create_or_convert_to_id(parent_id)
    data["visualParent"] = parent_id
    data["parents"] = parents

    return {
        "_id": _create_or_convert_to_id(entity_id),
        "type": "asset",
        "name": name,
        # This will be ignored
        "parent": project_id,
        "data": data,
        "schema": CURRENT_ASSET_DOC_SCHEMA
    }


def new_subset_document(name, family, asset_id, data=None, entity_id=None):
    """Create skeleton data of subset document.

    Args:
        name (str): Is considered as unique identifier of subset under asset.
        family (str): Subset's family.
        asset_id (Union[str, ObjectId]): Id of parent asset.
        data (Dict[str, Any]): Subset document data. Empty dictionary is used
            if not passed. Value of 'family' is used to fill 'family'.
        entity_id (Union[str, ObjectId]): Predefined id of document. New id is
            created if not passed.

    Returns:
        Dict[str, Any]: Skeleton of subset document.
    """

    if data is None:
        data = {}
    data["family"] = family
    return {
        "_id": _create_or_convert_to_id(entity_id),
        "schema": CURRENT_SUBSET_SCHEMA,
        "type": "subset",
        "name": name,
        "data": data,
        "parent": _create_or_convert_to_id(asset_id)
    }


def new_version_doc(version, subset_id, data=None, entity_id=None):
    """Create skeleton data of version document.

    Args:
        version (int): Is considered as unique identifier of version
            under subset.
        subset_id (Union[str, ObjectId]): Id of parent subset.
        data (Dict[str, Any]): Version document data.
        entity_id (Union[str, ObjectId]): Predefined id of document. New id is
            created if not passed.

    Returns:
        Dict[str, Any]: Skeleton of version document.
    """

    if data is None:
        data = {}

    return {
        "_id": _create_or_convert_to_id(entity_id),
        "schema": CURRENT_VERSION_SCHEMA,
        "type": "version",
        "name": int(version),
        "parent": _create_or_convert_to_id(subset_id),
        "data": data
    }


def new_hero_version_doc(version_id, subset_id, data=None, entity_id=None):
    """Create skeleton data of hero version document.

    Args:
        version_id (ObjectId): Is considered as unique identifier of version
            under subset.
        subset_id (Union[str, ObjectId]): Id of parent subset.
        data (Dict[str, Any]): Version document data.
        entity_id (Union[str, ObjectId]): Predefined id of document. New id is
            created if not passed.

    Returns:
        Dict[str, Any]: Skeleton of version document.
    """

    if data is None:
        data = {}

    return {
        "_id": _create_or_convert_to_id(entity_id),
        "schema": CURRENT_HERO_VERSION_SCHEMA,
        "type": "hero_version",
        "version_id": _create_or_convert_to_id(version_id),
        "parent": _create_or_convert_to_id(subset_id),
        "data": data
    }


def new_representation_doc(
    name, version_id, context, data=None, entity_id=None
):
    """Create skeleton data of asset document.

    Args:
        version (int): Is considered as unique identifier of version
            under subset.
        version_id (Union[str, ObjectId]): Id of parent version.
        context (Dict[str, Any]): Representation context used for fill template
            of to query.
        data (Dict[str, Any]): Representation document data.
        entity_id (Union[str, ObjectId]): Predefined id of document. New id is
            created if not passed.

    Returns:
        Dict[str, Any]: Skeleton of version document.
    """

    if data is None:
        data = {}

    return {
        "_id": _create_or_convert_to_id(entity_id),
        "schema": CURRENT_REPRESENTATION_SCHEMA,
        "type": "representation",
        "parent": _create_or_convert_to_id(version_id),
        "name": name,
        "data": data,

        # Imprint shortcut to context for performance reasons.
        "context": context
    }


def new_thumbnail_doc(data=None, entity_id=None):
    """Create skeleton data of thumbnail document.

    Args:
        data (Dict[str, Any]): Thumbnail document data.
        entity_id (Union[str, ObjectId]): Predefined id of document. New id is
            created if not passed.

    Returns:
        Dict[str, Any]: Skeleton of thumbnail document.
    """

    if data is None:
        data = {}

    return {
        "_id": _create_or_convert_to_id(entity_id),
        "type": "thumbnail",
        "schema": CURRENT_THUMBNAIL_SCHEMA,
        "data": data
    }


def new_workfile_info_doc(
    filename, asset_id, task_name, files, data=None, entity_id=None
):
    """Create skeleton data of workfile info document.

    Workfile document is at this moment used primarily for artist notes.

    Args:
        filename (str): Filename of workfile.
        asset_id (Union[str, ObjectId]): Id of asset under which workfile live.
        task_name (str): Task under which was workfile created.
        files (List[str]): List of rootless filepaths related to workfile.
        data (Dict[str, Any]): Additional metadata.

    Returns:
        Dict[str, Any]: Skeleton of workfile info document.
    """

    if not data:
        data = {}

    return {
        "_id": _create_or_convert_to_id(entity_id),
        "type": "workfile",
        "parent": _create_or_convert_to_id(asset_id),
        "task_name": task_name,
        "filename": filename,
        "data": data,
        "files": files
    }


def _prepare_update_data(old_doc, new_doc, replace):
    changes = {}
    for key, value in new_doc.items():
        if key not in old_doc or value != old_doc[key]:
            changes[key] = value

    if replace:
        for key in old_doc.keys():
            if key not in new_doc:
                changes[key] = REMOVED_VALUE
    return changes


def prepare_asset_update_data(old_doc, new_doc, replace=True):
    """Compare two subset documents and prepare update data.

    Based on compared values will create update data for
    'MongoUpdateOperation'.

    Empty output means that documents are identical.

    Returns:
        Dict[str, Any]: Changes between old and new document.
    """

    changes = {}
    for key, value in new_doc.items():
        if key in ("data", ):
            continue

        if key not in old_doc or value != old_doc[key]:
            changes[key] = value

    return _prepare_update_data(old_doc, new_doc, replace)


def prepare_subset_update_data(old_doc, new_doc, replace=True):
    """Compare two subset documents and prepare update data.

    Based on compared values will create update data for
    'MongoUpdateOperation'.

    Empty output means that documents are identical.

    Returns:
        Dict[str, Any]: Changes between old and new document.
    """

    return _prepare_update_data(old_doc, new_doc, replace)


def prepare_version_update_data(old_doc, new_doc, replace=True):
    """Compare two version documents and prepare update data.

    Based on compared values will create update data for
    'MongoUpdateOperation'.

    Empty output means that documents are identical.

    Returns:
        Dict[str, Any]: Changes between old and new document.
    """

    return _prepare_update_data(old_doc, new_doc, replace)


def prepare_hero_version_update_data(old_doc, new_doc, replace=True):
    """Compare two hero version documents and prepare update data.

    Based on compared values will create update data for 'UpdateOperation'.

    Empty output means that documents are identical.

    Returns:
        Dict[str, Any]: Changes between old and new document.
    """

    return _prepare_update_data(old_doc, new_doc, replace)


def prepare_representation_update_data(old_doc, new_doc, replace=True):
    """Compare two representation documents and prepare update data.

    Based on compared values will create update data for
    'MongoUpdateOperation'.

    Empty output means that documents are identical.

    Returns:
        Dict[str, Any]: Changes between old and new document.
    """

    return _prepare_update_data(old_doc, new_doc, replace)


def prepare_workfile_info_update_data(old_doc, new_doc, replace=True):
    """Compare two workfile info documents and prepare update data.

    Based on compared values will create update data for
    'MongoUpdateOperation'.

    Empty output means that documents are identical.

    Returns:
        Dict[str, Any]: Changes between old and new document.
    """

    return _prepare_update_data(old_doc, new_doc, replace)


class FailedOperations(Exception):
    pass


def entity_data_json_default(value):
    if isinstance(value, datetime.datetime):
        return int(value.timestamp())

    raise TypeError(
        "Object of type {} is not JSON serializable".format(str(type(value)))
    )


class ServerCreateOperation(CreateOperation):
    """Opeartion to create an entity.

    Args:
        project_name (str): On which project operation will happen.
        entity_type (str): Type of entity on which change happens.
            e.g. 'asset', 'representation' etc.
        data (Dict[str, Any]): Data of entity that will be created.
    """

    def __init__(self, project_name, entity_type, data, session):
        self._session = session

        if not data:
            data = {}
        data = copy.deepcopy(data)
        if entity_type == "project":
            raise ValueError("Project cannot be created using operations")

        if entity_type == "hero_version":
            raise ValueError("Hero version cannot be created using operations")

        tasks = None
        if entity_type in "asset":
            # TODO handle tasks
            entity_type = "folder"
            if "data" in data:
                tasks = data["data"].get("tasks")

            project = self._session.get_project(project_name)
            new_data = convert_create_asset_to_v4(data, project, self.con)

        elif entity_type == "task":
            project = self._session.get_project(project_name)
            new_data = convert_create_task_to_v4(data, project, self.con)

        elif entity_type == "subset":
            new_data = convert_create_subset_to_v4(data, self.con)

        elif entity_type == "version":
            new_data = convert_create_version_to_v4(data, self.con)

        elif entity_type == "representation":
            new_data = convert_create_representation_to_v4(data, self.con)

        else:
            raise ValueError("Unhandled entity type \"{}\"".format(entity_type))

        # Simple check if data can be dumped into json
        #   - should raise error on 'ObjectId' object
        try:
            new_data = json.loads(
                json.dumps(new_data, default=entity_data_json_default)
            )
        except:
            print(json.dumps(
                new_data,
                default=lambda item: "< This Failed: {}>".format(str(item))))
            raise

        super(ServerCreateOperation, self).__init__(
            project_name, entity_type, new_data
        )

        if "id" not in self._data:
            self._data["id"] = create_entity_id()

        if tasks:
            copied_tasks = copy.deepcopy(tasks)
            for task_name, task in copied_tasks.items():
                task["name"] = task_name
                task["folderId"] = self._data["id"]
                self.session.create_entity(
                    project_name, "task", task, nested_id=self.id
                )

    @property
    def con(self):
        return self.session.con

    @property
    def session(self):
        return self._session

    @property
    def entity_id(self):
        return self._data["id"]

    def to_server_operation(self):
        return {
            "id": self.id,
            "type": "create",
            "entityType": self.entity_type,
            "entityId": self.entity_id,
            "data": self._data
        }


class ServerUpdateOperation(UpdateOperation):
    """Operation to update an entity.

    Args:
        project_name (str): On which project operation will happen.
        entity_type (str): Type of entity on which change happens.
            e.g. 'asset', 'representation' etc.
        entity_id (Union[str, ObjectId]): Identifier of an entity.
        update_data (Dict[str, Any]): Key -> value changes that will be set in
            database. If value is set to 'REMOVED_VALUE' the key will be
            removed. Only first level of dictionary is checked (on purpose).
    """

    def __init__(
        self, project_name, entity_type, entity_id, update_data, session
    ):
        self._session = session

        update_data = copy.deepcopy(update_data)
        if entity_type == "project":
            raise ValueError("Project cannot be created using operations")

        if entity_type == "asset":
            raise ValueError(
                "Update operations for assets are not implemented yet"
            )

        elif entity_type == "subset":
            new_update_data = convert_update_subset_to_v4(
                project_name, entity_id, update_data, self.con
            )

        elif entity_type == "version":
            new_update_data = convert_update_version_to_v4(
                project_name, entity_id, update_data, self.con
            )

        elif entity_type == "representation":
            new_update_data = convert_update_representation_to_v4(
                project_name, entity_id, update_data, self.con
            )

        else:
            raise ValueError("Unhandled entity type \"{}\"".format(entity_type))

        super(ServerUpdateOperation, self).__init__(
            project_name, entity_type, entity_id, new_update_data
        )

    @property
    def con(self):
        return self.session.con

    @property
    def session(self):
        return self._session

    def to_server_operation(self):
        if not self._update_data:
            return None

        update_data = {}
        for key, value in self._update_data.items():
            if value is REMOVED_VALUE:
                value = None
            update_data[key] = value

        return {
            "id": self.id,
            "type": "update",
            "entityType": self.entity_type,
            "entityId": self.entity_id,
            "data": update_data
        }


class ServerDeleteOperation(DeleteOperation):
    """Opeartion to delete an entity.

    Args:
        project_name (str): On which project operation will happen.
        entity_type (str): Type of entity on which change happens.
            e.g. 'asset', 'representation' etc.
        entity_id (Union[str, ObjectId]): Entity id that will be removed.
    """

    def __init__(self, project_name, entity_type, entity_id, session):
        self._session = session

        if entity_type == "asset":
            entity_type == "folder"

        super(ServerDeleteOperation, self).__init__(
            project_name, entity_type, entity_id
        )

    @property
    def con(self):
        return self.session.con

    @property
    def session(self):
        return self._session

    def to_server_operation(self):
        return {
            "id": self.id,
            "type": self.operation_name,
            "entityId": self.entity_id,
            "entityType": self.entity_type,
        }


class OperationsSession(BaseOperationsSession):
    def __init__(self, con=None, *args, **kwargs):
        super(OperationsSession, self).__init__(*args, **kwargs)
        if con is None:
            con = get_server_api_connection()
        self._con = con
        self._project_cache = {}
        self._nested_operations = collections.defaultdict(list)

    @property
    def con(self):
        return self._con

    def get_project(self, project_name):
        if project_name not in self._project_cache:
            self._project_cache[project_name] = self.con.get_project(
                project_name)
        return copy.deepcopy(self._project_cache[project_name])

    def commit(self):
        """Commit session operations."""

        operations, self._operations = self._operations, []
        if not operations:
            return

        operations_by_project = collections.defaultdict(list)
        for operation in operations:
            operations_by_project[operation.project_name].append(operation)

        body_by_id = {}
        results = []
        for project_name, operations in operations_by_project.items():
            operations_body = []
            for operation in operations:
                body = operation.to_server_operation()
                if body is not None:
                    body_by_id[operation.id] = body
                    operations_body.append(body)

            if operations_body:
                result = self._con.post(
                    "projects/{}/operations".format(project_name),
                    operations=operations_body,
                    canFail=False
                )
                results.append(result.data)

        for result in results:
            if result["success"]:
                continue

            if "operations" not in result:
                raise FailedOperations(
                    "Operation failed. Content: {}".format(str(result))
                )

            for op_result in result["operations"]:
                if not op_result["success"]:
                    operation_id = op_result["id"]
                    raise FailedOperations((
                        "Operation \"{}\" failed with data:\n{}\nError: {}."
                    ).format(
                        operation_id,
                        json.dumps(body_by_id[operation_id], indent=4),
                        op_result["error"],
                    ))

    def create_entity(self, project_name, entity_type, data, nested_id=None):
        """Fast access to 'MongoCreateOperation'.

        Args:
            project_name (str): On which project the creation happens.
            entity_type (str): Which entity type will be created.
            data (Dicst[str, Any]): Entity data.
            nested_id (str): Id of other operation from which is triggered
                operation -> Operations can trigger suboperations but they
                must be added to operations list after it's parent is added.

        Returns:
            MongoCreateOperation: Object of update operation.
        """

        if entity_type == "hero_version":
            return None

        operation = ServerCreateOperation(
            project_name, entity_type, data, self
        )

        if nested_id:
            self._nested_operations[nested_id].append(operation)
        else:
            self.add(operation)
            if operation.id in self._nested_operations:
                self.extend(self._nested_operations.pop(operation.id))

        return operation

    def update_entity(
        self, project_name, entity_type, entity_id, update_data, nested_id=None
    ):
        """Fast access to 'MongoUpdateOperation'.

        Returns:
            MongoUpdateOperation: Object of update operation.
        """

        operation = ServerUpdateOperation(
            project_name, entity_type, entity_id, update_data, self
        )
        if nested_id:
            self._nested_operations[nested_id].append(operation)
        else:
            self.add(operation)
            if operation.id in self._nested_operations:
                self.extend(self._nested_operations.pop(operation.id))
        return operation

    def delete_entity(
        self, project_name, entity_type, entity_id, nested_id=None
    ):
        """Fast access to 'MongoDeleteOperation'.

        Returns:
            MongoDeleteOperation: Object of delete operation.
        """

        operation = ServerDeleteOperation(
            project_name, entity_type, entity_id, self
        )
        if nested_id:
            self._nested_operations[nested_id].append(operation)
        else:
            self.add(operation)
            if operation.id in self._nested_operations:
                self.extend(self._nested_operations.pop(operation.id))
        return operation


def create_project(
    project_name,
    project_code,
    library_project=False,
    preset_name=None,
    con=None
):
    """Create project using OpenPype settings.

    This project creation function is not validating project document on
    creation. It is because project document is created blindly with only
    minimum required information about project which is it's name, code, type
    and schema.

    Entered project name must be unique and project must not exist yet.

    Note:
        This function is here to be OP v4 ready but in v3 has more logic
            to do. That's why inner imports are in the body.

    Args:
        project_name (str): New project name. Should be unique.
        project_code (str): Project's code should be unique too.
        library_project (bool): Project is library project.
        preset_name (str): Name of anatomy preset. Default is used if not
            passed.
        con (ServerAPI): Connection to server with logged user.

    Raises:
        ValueError: When project name already exists in MongoDB.

    Returns:
        dict: Created project document.
    """

    if con is None:
        con = get_server_api_connection()

    if con.get_project(project_name, fields=["name"]):
        raise ValueError("Project with name \"{}\" already exists".format(
            project_name
        ))

    if not PROJECT_NAME_REGEX.match(project_name):
        raise ValueError((
            "Project name \"{}\" contain invalid characters"
        ).format(project_name))

    preset = con.get_project_anatomy_preset(preset_name)
    config = {
        "templates": preset["templates"],
        "roots": preset["roots"]
    }
    folder_types = {}
    for folder_type in preset["folder_types"]:
        name = folder_type.pop("name")
        folder_types[name] = folder_type

    task_types = {}
    for task_type in preset["task_types"]:
        name = task_type.pop("name")
        task_types[name] = task_type

    result = con.put(
        "projects/{}".format(project_name),
        code=project_code,
        library=library_project,
        config=config,
        attrib=preset["attributes"],
        folderTypes=folder_types,
        taskTypes=task_types
    )
    if result.status != 201:
        details = "Unknown details ({})".format(result.status)
        if result.data:
            details = result.data.get("detail") or details
        raise ValueError("Failed to create project \"{}\": {}".format(
            project_name, details
        ))

    return con.get_project(project_name)


def delete_project(project_name, con=None):
    if con is None:
        con = get_server_api_connection()

    if not con.get_project(project_name, fields=["name"]):
        raise ValueError("Project with name \"{}\" was not found".format(
            project_name
        ))

    result = con.delete("projects/{}".format(project_name))
    if result.status_code != 204:
        raise ValueError(
            "Failed to delete project \"{}\". {}".format(
                project_name, result.data["detail"]
            )
        )