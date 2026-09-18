from mstrio.api import subscription_assets as subscription_assets_api
from mstrio.connection import Connection
from mstrio.utils import helper, time_helper
from mstrio.utils.entity import EntityBase
from mstrio.utils.response_processors import subscription_assets


class _SubscriptionAsset(EntityBase):
    """Base class for image and Excel template assets."""

    _API_GETTERS = {}
    _FROM_DICT_MAP = {
        'date_created': time_helper.DatetimeFormats.FULLDATETIME,
        'date_modified': time_helper.DatetimeFormats.FULLDATETIME,
    }
    _PATCH_PATH_TYPES = {'name': str, 'description': str}
    _PATCH_API = None
    _UPDATE_API = None
    _CREATE_API = None
    _ASSET_NAME = 'asset'
    _ID_ATTRIBUTE = 'asset_id'

    def __init__(self, connection: Connection, id: str | None = None):
        if not id:
            raise ValueError(f'{self.__class__.__name__} ID must be provided.')
        super().__init__(connection, id)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        setattr(self, self._ID_ATTRIBUTE, kwargs.get('id', default_value))
        self.description = kwargs.get('description', default_value)
        self.date_created = time_helper.map_str_to_datetime(
            'date_created', kwargs.get('date_created'), self._FROM_DICT_MAP
        )
        self.date_modified = time_helper.map_str_to_datetime(
            'date_modified', kwargs.get('date_modified'), self._FROM_DICT_MAP
        )
        self.hidden = kwargs.get('hidden', default_value)
        self.binary = kwargs.get('binary', default_value)

    @classmethod
    def _create(
        cls,
        connection: Connection,
        name: str,
        description: str | None,
        file,
    ):
        response = cls._CREATE_API(
            connection=connection,
            name=name,
            description=description,
            file=file,
        )
        return cls.from_dict(response.json(), connection)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Partially update asset metadata."""
        body = helper.delete_none_values(
            {'name': name, 'description': description},
            recursion=True,
        )
        if not body:
            return

        response = self._PATCH_API(
            connection=self.connection,
            **{f'{self._ASSET_NAME}_id': self.id},
            body=body,
        )
        if response.ok:
            self._set_object_attributes(**body)

    patch = alter

    def update(
        self,
        name: str,
        description: str | None = None,
        file=None,
    ):
        """Replace the asset metadata and binary content."""
        response = self._UPDATE_API(
            connection=self.connection,
            **{f'{self._ASSET_NAME}_id': self.id},
            name=name,
            description=description,
            file=file,
        )
        if response.ok:
            self._set_object_attributes(**response.json())
        return self

    def delete(self, force: bool = False) -> bool:
        """Delete the asset."""
        if not force:
            answer = input(
                f'Are you sure you want to delete {self._ASSET_NAME} '
                f"'{self.name}' with ID: {self.id}? [Y/N]: "
            )
            if answer != 'Y':
                return False

        response = (
            subscription_assets_api.remove_image(self.connection, image_id=self.id)
            if self._ASSET_NAME == 'image'
            else subscription_assets_api.remove_excel_template(
                self.connection, excel_template_id=self.id
            )
        )
        return response.ok


class Image(_SubscriptionAsset):
    """Strategy subscription image."""

    _ASSET_NAME = 'image'
    _ID_ATTRIBUTE = 'image_id'
    _API_GETTERS = {
        (
            'id',
            'name',
            'description',
            'date_created',
            'date_modified',
            'hidden',
            'binary',
        ): subscription_assets_api.get_image
    }
    _PATCH_API = staticmethod(subscription_assets_api.patch_image)
    _UPDATE_API = staticmethod(subscription_assets_api.update_image)
    _CREATE_API = staticmethod(subscription_assets_api.create_image)

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        description: str | None,
        file,
    ):
        """Create an image."""
        return cls._create(connection, name, description, file)


def list_images(
    connection: Connection,
    to_dictionary: bool = False,
    include_hidden: bool = False,
) -> list[Image] | list[dict]:
    """List subscription images."""
    images = subscription_assets.list_images(connection, include_hidden)
    if to_dictionary:
        return images
    return Image.bulk_from_dict(source_list=images, connection=connection)


def get_image(connection: Connection, id: str) -> Image:
    """Get an image by ID."""
    response = subscription_assets_api.get_image(connection, image_id=id)
    return Image.from_dict(response.json(), connection)


class ExcelTemplate(_SubscriptionAsset):
    """Strategy subscription Excel template."""

    _ASSET_NAME = 'excel_template'
    _ID_ATTRIBUTE = 'excel_template_id'
    _API_GETTERS = {
        (
            'id',
            'name',
            'description',
            'date_created',
            'date_modified',
            'hidden',
            'sheet_names',
        ): subscription_assets_api.get_excel_template
    }
    _PATCH_API = staticmethod(subscription_assets_api.patch_excel_template)
    _UPDATE_API = staticmethod(subscription_assets_api.update_excel_template)
    _CREATE_API = staticmethod(subscription_assets_api.create_excel_template)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.sheet_names = kwargs.get('sheet_names', default_value)

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        description: str | None,
        file,
    ):
        """Create an Excel template."""
        return cls._create(connection, name, description, file)


def list_excel_templates(
    connection: Connection,
    to_dictionary: bool = False,
    include_hidden: bool = False,
) -> list[ExcelTemplate] | list[dict]:
    """List subscription Excel templates."""
    templates = subscription_assets.list_excel_templates(connection, include_hidden)
    if to_dictionary:
        return templates
    return ExcelTemplate.bulk_from_dict(source_list=templates, connection=connection)


def get_excel_template(
    connection: Connection,
    id: str,
    show_sheets: bool = True,
) -> ExcelTemplate:
    """Get an Excel template by ID."""
    response = subscription_assets_api.get_excel_template(
        connection,
        excel_template_id=id,
        show_sheets=show_sheets,
    )
    return ExcelTemplate.from_dict(response.json(), connection)
