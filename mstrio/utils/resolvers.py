import typing as t

from mstrio.api import projects as projects_api

if t.TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.server import Project


T = t.TypeVar('T')


# --- PARAMETERS Resolvers ---
def _get_id_from_params_set(
    object: T | str | None,
    object_id: str | None,
    object_prop: str | None,
    object_class: type[T],
    object_listing_method: t.Callable[[], list[T | dict]],
    fallback_value: str | None = None,
    property_name: str = 'name',
) -> str | None:
    """
    Utility function to get an object's ID from a set of parameters.

    Should be used inside a method that has a set of parameters that can hold
    the object's ID, but only one of those is required to be passed.

    Example:
        >>> # Method signature
        >>> def some_method(
        >>>     self,
        >>>     conn: Connection,
        >>>     project: Project | None = None,
        >>>     project_id: str | None = None,
        >>>     project_name: str | None = None,
        >>>     ...
        >>> ): ...
        >>>
        >>> # Method body
        >>> project_id = get_id_from_params_set(
        >>>     project,
        >>>     project_id,
        >>>     project_name,
        >>>     Project,
        >>>     lambda: list_projects(conn),
        >>>     fallback_value=conn.project_id,
        >>> )
        >>> ...

    Args:
        object: An instance of the `object_class` or its ID or name.
        object_id: ID of the object.
        object_prop: `property_name` of the object.
        object_class: The class of the object.
        object_listing_method: A method that returns a list of all objects of
            the given type.
        fallback_value: A value to return if none of the parameters are set.
        property_name: The name of the property to use for matching.

    Returns:
        The ID of the object if found, otherwise the `fallback_value`.
    """

    if object is not None:
        if isinstance(object, object_class):
            return object.id
        return _get_id_from_params_set(
            object=None,
            object_id=object,  # assume ID was provided as `object`
            object_prop=None,
            object_class=object_class,
            object_listing_method=object_listing_method,
            fallback_value=fallback_value,
            property_name=property_name,
        )
    if object_id is not None:
        from mstrio.utils.helper import is_valid_str_id

        if is_valid_str_id(object_id):
            return object_id
        return _get_id_from_params_set(
            object=None,
            object_id=None,
            object_prop=object_id,  # assume `object_prop` was provided as `object_id`
            object_class=object_class,
            object_listing_method=object_listing_method,
            fallback_value=fallback_value,
            property_name=property_name,
        )
    if object_prop is not None:
        items = object_listing_method()

        assert isinstance(items, (list, tuple)), (
            f"Expected listing method to return a list or tuple, "
            f"but found: {type(items).__name__}"
        )
        assert all(isinstance(obj, (object_class, dict)) for obj in items), (
            f"Expected all objects to be of type {object_class.__name__} or pure dicts,"
            f" but found types are: {{type(obj).__name__ for obj in items}}"
        )

        def get_prop_val(itm):
            if isinstance(itm, object_class):
                return getattr(itm, property_name, None)
            return itm.get(property_name)

        valid_objects = [obj for obj in items if get_prop_val(obj) == object_prop]

        assert len(valid_objects) == 1, (
            f"Could not uniquely identify the {object_class.__name__} "
            f"by it's {property_name} '{object_prop}'. "
            f"Found {len(valid_objects)} items. "
            f"Please provide a {object_class.__name__} class instance or ID instead."
        )

        itm = valid_objects[0]
        return itm.id if isinstance(itm, object_class) else itm.get('id')

    return fallback_value


def get_project_id_from_params_set(
    conn: 'Connection | None',
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    assert_id_exists: bool = True,
    no_fallback_from_connection: bool = False,
) -> str | None:
    """
    Utility function to get a project's ID from a set of parameters.

    Should be used inside a method that has a set of parameters that can hold
    the project's ID, but only one of those is required to be passed.

    Args:
        conn: A Strategy connection object.
        project: An instance of the `Project` class or its ID or name.
        project_id: ID of the project.
        project_name: Name of the project.
        assert_id_exists: If `False`, return `None` if no project is found.
            If `True`, raises an `AssertionError` if no project is found.
        no_fallback_from_connection: If `True`, the function will return `None`
            instead of the connection's default project ID if no project is
            found.

    Returns:
        The ID of the project if found, otherwise the connection's default
        project ID, unless `no_fallback_from_connection` is True.
    """

    from mstrio.server import Project

    try:
        ret = _get_id_from_params_set(
            project,
            project_id,
            project_name,
            Project,
            lambda: projects_api.get_projects(conn).json() if conn else [],
            fallback_value=(
                conn.project_id if not no_fallback_from_connection and conn else None
            ),
        )
    except AssertionError as err:
        raise ValueError(err) from err

    if assert_id_exists and not ret:
        from mstrio.utils.helper import exception_handler

        msg = (
            "Could not determine the project ID. Please provide a Project "
            "class instance or ID directly."
        )
        exception_handler(msg, exception_type=ValueError)

    return ret


# FYI: Copy-pastable parts for project-related parameters:
"""
[params to the method]
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,

[DOCSTRING for "Args" part]
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name

[implementation of usual use]
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
        )
"""

# TODO: add params `project_id` and `project_name` to where
# we have only `project`

# --- END: PARAMETERS Resolvers ---


# --- FILTERS KWARGS Resolvers ---
def validate_owner_key_in_filters(filters_kwargs: dict[str, t.Any]) -> None:
    """Validate if `owner` filter kwarg is in valid shape.

    Note:
        REST requires the shape to be `{'id': <id>}`. However, not everywhere!
        There are places where `owner` needs to be an ID and places where it
        needs to be string of exact match on name. Use at your own discretion.

    Note:
        This method does not return a value, it modifies the input dict
        in-place!

    Args:
        filters_kwargs: Dictionary of filter kwargs to validate `owner` in.
    """
    if 'owner' not in filters_kwargs:
        return  # NOOP

    val = filters_kwargs['owner']
    if val is None:
        del filters_kwargs['owner']
        return

    from mstrio.utils.entity import Entity

    if isinstance(val, Entity):
        # We do not care for more specific module than `Entity`
        # REST will handle invalid ID
        val = val.id

    if isinstance(val, str):
        filters_kwargs['owner'] = {"id": val}
        return

    if isinstance(val, dict) and "id" in val:
        filters_kwargs['owner'] = {"id": val["id"]}  # sanitize: remove other keys
        return

    raise AttributeError(
        "`owner` filter has incorrect value. It should be a class instance, "
        "item ID as string or dict in a shape `{'id': <id>}`"
    )


# --- END: FILTERS KWARGS Resolvers ---
