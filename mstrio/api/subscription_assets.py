from typing import TYPE_CHECKING

from requests import Response

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


def _multipart_data(name: str | None, description: str | None) -> dict:
    return {
        key: value
        for key, value in {'name': name, 'description': description}.items()
        if value is not None
    }


@ErrorHandler(err_msg='Error listing images')
def list_images(
    connection: 'Connection',
    include_hidden: bool = False,
    error_msg: str | None = None,
) -> Response:
    """List images available to the authenticated user."""
    return connection.get(
        endpoint='/api/subscriptions/images',
        params={'includeHidden': include_hidden},
    )


@ErrorHandler(err_msg='Error getting image {image_id}')
def get_image(
    connection: 'Connection',
    image_id: str,
    error_msg: str | None = None,
) -> Response:
    """Get an image by ID."""
    return connection.get(endpoint=f'/api/subscriptions/images/{image_id}')


@ErrorHandler(err_msg='Error creating image')
def create_image(
    connection: 'Connection',
    name: str,
    description: str | None,
    file,
    error_msg: str | None = None,
) -> Response:
    """Create an image from multipart form data."""
    return connection.post(
        endpoint='/api/subscriptions/images',
        data=_multipart_data(name, description),
        files={'file': file},
    )


@ErrorHandler(err_msg='Error updating image {image_id}')
def update_image(
    connection: 'Connection',
    image_id: str,
    name: str | None,
    description: str | None,
    file,
    error_msg: str | None = None,
) -> Response:
    """Replace an image using multipart form data."""
    return connection.put(
        endpoint=f'/api/subscriptions/images/{image_id}',
        data=_multipart_data(name, description),
        files={'file': file},
    )


@ErrorHandler(err_msg='Error partially updating image {image_id}')
def patch_image(
    connection: 'Connection',
    image_id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Partially update image metadata."""
    return connection.patch(
        endpoint=f'/api/subscriptions/images/{image_id}',
        json=body,
    )


@ErrorHandler(err_msg='Error removing image {image_id}')
def remove_image(
    connection: 'Connection',
    image_id: str,
    error_msg: str | None = None,
) -> Response:
    """Remove an image by ID."""
    return connection.delete(endpoint=f'/api/subscriptions/images/{image_id}')


@ErrorHandler(err_msg='Error listing Excel templates')
def list_excel_templates(
    connection: 'Connection',
    include_hidden: bool = False,
    error_msg: str | None = None,
) -> Response:
    """List Excel templates available to the authenticated user."""
    return connection.get(
        endpoint='/api/excelTemplates',
        params={'includeHidden': include_hidden},
    )


@ErrorHandler(err_msg='Error getting Excel template {excel_template_id}')
def get_excel_template(
    connection: 'Connection',
    excel_template_id: str,
    show_sheets: bool = True,
    error_msg: str | None = None,
) -> Response:
    """Get an Excel template by ID."""
    return connection.get(
        endpoint=f'/api/excelTemplates/{excel_template_id}',
        params={'sheets': show_sheets},
    )


@ErrorHandler(err_msg='Error creating Excel template')
def create_excel_template(
    connection: 'Connection',
    name: str,
    description: str | None,
    file,
    error_msg: str | None = None,
) -> Response:
    """Create an Excel template from multipart form data."""
    return connection.post(
        endpoint='/api/excelTemplates',
        data=_multipart_data(name, description),
        files={'file': file},
    )


@ErrorHandler(err_msg='Error updating Excel template {excel_template_id}')
def update_excel_template(
    connection: 'Connection',
    excel_template_id: str,
    name: str | None,
    description: str | None,
    file,
    error_msg: str | None = None,
) -> Response:
    """Replace an Excel template using multipart form data."""
    return connection.put(
        endpoint=f'/api/excelTemplates/{excel_template_id}',
        data=_multipart_data(name, description),
        files={'file': file},
    )


@ErrorHandler(err_msg='Error partially updating Excel template {excel_template_id}')
def patch_excel_template(
    connection: 'Connection',
    excel_template_id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Partially update Excel template metadata."""
    return connection.patch(
        endpoint=f'/api/excelTemplates/{excel_template_id}',
        json=body,
    )


@ErrorHandler(err_msg='Error removing Excel template {excel_template_id}')
def remove_excel_template(
    connection: 'Connection',
    excel_template_id: str,
    error_msg: str | None = None,
) -> Response:
    """Remove an Excel template by ID."""
    return connection.delete(endpoint=f'/api/excelTemplates/{excel_template_id}')
