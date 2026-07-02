import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import data_models
from mstrio.connection import Connection
from mstrio.modeling.data_model.data_model_component import DataModelComponent
from mstrio.modeling.data_model.helpers import unpack_information_dict
from mstrio.utils.helper import delete_none_values
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.modeling.data_model.data_model import DataModel

logger = logging.getLogger(__name__)


@method_version_handler('11.6.0100')
def list_data_model_metrics(
    connection: Connection,
    data_model: 'DataModel | str',
    to_dictionary: bool = False,
    limit: int | None = None,
    offset: int | None = None,
    show_expression_as: str | None = None,
    show_filter_tokens: bool | None = None,
    fields: str | None = None,
    changeset_id: str | None = None,
) -> list['DataModelMetric'] | list[dict]:
    """Get a list of metrics of a Mosaic data model.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        data_model (DataModel | str): data model object or its ID
        to_dictionary (bool, optional): if True, return metrics as
            a list of dicts
        limit (int, optional): limit the number of elements returned
        offset (int, optional): starting point within the collection
        show_expression_as (str, optional): specify how expressions are
            presented ('tree' or 'tokens')
        show_filter_tokens (bool, optional): whether to show filter
            expressions as tokens
        fields (str, optional): comma-separated top-level field whitelist
        changeset_id (str, optional): ID of an existing changeset to read from

    Returns:
        A list of DataModelMetric objects or dictionaries representing them.
    """
    data_model_id = data_model if isinstance(data_model, str) else data_model.id
    metrics = (
        data_models.list_data_model_metrics(
            connection,
            id=data_model_id,
            changeset_id=changeset_id,
            offset=offset,
            limit=limit,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
            fields=fields,
        )
        .json()
        .get('metrics', [])
    )
    if limit:
        metrics = metrics[:limit]
    if to_dictionary:
        return [unpack_information_dict(metric) for metric in metrics]
    return [
        DataModelMetric._from_api_source(connection, data_model_id, metric)
        for metric in metrics
    ]


@method_version_handler('11.6.0100')
def list_data_model_fact_metrics(
    connection: Connection,
    data_model: 'DataModel | str',
    to_dictionary: bool = False,
    limit: int | None = None,
    offset: int | None = None,
    show_expression_as: str | None = None,
    fields: str | None = None,
    changeset_id: str | None = None,
) -> list['DataModelFactMetric'] | list[dict]:
    """Get a list of fact metrics of a Mosaic data model.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        data_model (DataModel | str): data model object or its ID
        to_dictionary (bool, optional): if True, return fact metrics as
            a list of dicts
        limit (int, optional): limit the number of elements returned
        offset (int, optional): starting point within the collection
        show_expression_as (str, optional): specify how expressions are
            presented ('tree' or 'tokens')
        fields (str, optional): comma-separated top-level field whitelist
        changeset_id (str, optional): ID of an existing changeset to read from

    Returns:
        A list of DataModelFactMetric objects or dictionaries representing
        them.
    """
    data_model_id = data_model if isinstance(data_model, str) else data_model.id
    fact_metrics = (
        data_models.list_data_model_fact_metrics(
            connection,
            id=data_model_id,
            changeset_id=changeset_id,
            offset=offset,
            limit=limit,
            show_expression_as=show_expression_as,
            fields=fields,
        )
        .json()
        .get('factMetrics', [])
    )
    if limit:
        fact_metrics = fact_metrics[:limit]
    if to_dictionary:
        return [unpack_information_dict(metric) for metric in fact_metrics]
    return [
        DataModelFactMetric._from_api_source(connection, data_model_id, metric)
        for metric in fact_metrics
    ]


@class_version_handler('11.6.0100')
class DataModelMetric(DataModelComponent):
    """Python representation of an (advanced) metric of a Mosaic data
    model."""

    _ACL_SUBTYPE = 'metric'
    _GET_FUNC = staticmethod(data_models.get_data_model_metric)
    _DELETE_FUNC = staticmethod(data_models.delete_data_model_metric)
    _ID_KWARG = 'metric_id'

    @classmethod
    def create(
        cls,
        connection: Connection,
        data_model: 'DataModel | str',
        name: str,
        expression: dict | None = None,
        description: str | None = None,
        definition: dict | None = None,
        show_expression_as: str | None = None,
        show_filter_tokens: bool | None = None,
        show_advanced_properties: bool | None = None,
    ) -> 'DataModelMetric':
        """Create a new metric in a Mosaic data model.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            data_model (DataModel | str): data model object or its ID
            name (str): name of the metric
            expression (dict, optional): metric expression
                (`ms-Expression` schema)
            description (str, optional): description of the metric
            definition (dict, optional): additional top-level body keys of the
                `ms-AdvancedMetric` schema merged into the request body (e.g.
                `dimty`, `conditionality`, `metricSubtotals`)
            show_expression_as (str, optional): specify how expressions are
                presented in the response ('tree' or 'tokens')
            show_filter_tokens (bool, optional): whether to show filter
                expressions as tokens
            show_advanced_properties (bool, optional): whether to show
                advanced properties in the response

        Returns:
            DataModelMetric object.
        """
        data_model_id = data_model if isinstance(data_model, str) else data_model.id
        body = {
            'name': name,
            'description': description,
            'expression': expression,
            **(definition or {}),
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.create_data_model_metric(
            connection,
            id=data_model_id,
            body=body,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
            show_advanced_properties=show_advanced_properties,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created metric named: '{name}' with ID: '"
                f"{response.get('id')}' in data model '{data_model_id}'."
            )
        return cls._from_api_source(connection, data_model_id, response)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        expression: dict | None = None,
        definition: dict | None = None,
    ) -> None:
        """Alter the metric.

        Note:
            The underlying endpoint is a PUT (full replace). This method
            first fetches the current definition and merges the requested
            changes into it before sending, so unspecified fields are
            preserved.

        Args:
            name (str, optional): new name of the metric
            description (str, optional): new description of the metric
            expression (dict, optional): new metric expression
            definition (dict, optional): additional top-level body keys merged
                into the request body
        """
        current = (
            type(self)
            ._GET_FUNC(self.connection, id=self.data_model_id, metric_id=self.id)
            .json()
        )
        body = {key: val for key, val in current.items() if key != 'id'}
        changes = {
            'name': name,
            'description': description,
            'expression': expression,
            **(definition or {}),
        }
        body.update(delete_none_values(changes, recursion=False))
        response = data_models.update_data_model_metric(
            self.connection, id=self.data_model_id, metric_id=self.id, body=body
        )
        self._set_object_attributes(**unpack_information_dict(response.json()))
        if config.verbose:
            logger.info(
                f"Successfully altered metric with ID: '{self.id}' in data "
                f"model '{self.data_model_id}'."
            )

    def get_applicable_advanced_properties(
        self, show_sql_preview: bool | None = None
    ) -> dict:
        """Get the advanced (VLDB) properties applicable to the metric.

        Args:
            show_sql_preview (bool, optional): whether to include a SQL
                preview in the response

        Returns:
            Dictionary with the applicable advanced properties.
        """
        return data_models.get_metric_applicable_advanced_properties(
            self.connection,
            id=self.data_model_id,
            metric_id=self.id,
            show_sql_preview=show_sql_preview,
        ).json()

    def create_embedded_object(
        self,
        body: dict,
        show_expression_as: str | None = None,
        show_filter_tokens: bool | None = None,
    ) -> dict:
        """Create an embedded object of the metric.

        Args:
            body (dict): embedded object definition
                (`ms-DataModelEmbeddedObject` schema)
            show_expression_as (str, optional): specify how expressions are
                presented in the response ('tree' or 'tokens')
            show_filter_tokens (bool, optional): whether to show filter
                expressions as tokens

        Returns:
            Dictionary with the created embedded object.
        """
        return data_models.create_metric_embedded_object(
            self.connection,
            id=self.data_model_id,
            metric_id=self.id,
            body=body,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
        ).json()

    def get_embedded_object(
        self,
        embedded_object_id: str,
        show_expression_as: str | None = None,
        show_filter_tokens: bool | None = None,
    ) -> dict:
        """Get an embedded object of the metric.

        Args:
            embedded_object_id (str): ID of the embedded object
            show_expression_as (str, optional): specify how expressions are
                presented ('tree' or 'tokens')
            show_filter_tokens (bool, optional): whether to show filter
                expressions as tokens

        Returns:
            Dictionary with the embedded object definition.
        """
        return data_models.get_metric_embedded_object(
            self.connection,
            id=self.data_model_id,
            metric_id=self.id,
            embedded_object_id=embedded_object_id,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
        ).json()

    def update_embedded_object(
        self,
        embedded_object_id: str,
        body: dict,
        show_expression_as: str | None = None,
        show_filter_tokens: bool | None = None,
    ) -> dict:
        """Update an embedded object of the metric (PUT, full replace).

        Args:
            embedded_object_id (str): ID of the embedded object
            body (dict): full embedded object definition
            show_expression_as (str, optional): specify how expressions are
                presented in the response ('tree' or 'tokens')
            show_filter_tokens (bool, optional): whether to show filter
                expressions as tokens

        Returns:
            Dictionary with the updated embedded object.
        """
        return data_models.update_metric_embedded_object(
            self.connection,
            id=self.data_model_id,
            metric_id=self.id,
            embedded_object_id=embedded_object_id,
            body=body,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
        ).json()


@class_version_handler('11.6.0100')
class DataModelFactMetric(DataModelComponent):
    """Python representation of a fact metric of a Mosaic data model."""

    _ACL_SUBTYPE = 'fact_metric'
    _GET_FUNC = staticmethod(data_models.get_data_model_fact_metric)
    _DELETE_FUNC = staticmethod(data_models.delete_data_model_fact_metric)
    _ID_KWARG = 'fact_metric_id'

    @classmethod
    def create(
        cls,
        connection: Connection,
        data_model: 'DataModel | str',
        name: str,
        fact: dict | None = None,
        function: str | None = None,
        description: str | None = None,
        definition: dict | None = None,
        show_expression_as: str | None = None,
        show_advanced_properties: bool | None = None,
        allow_link: bool | None = None,
    ) -> 'DataModelFactMetric':
        """Create a new fact metric in a Mosaic data model.

        Note:
            This endpoint also creates compound, conditional and
            transformation metrics - the differentiator is which top-level
            body keys are set (e.g. `fact` + `function` for a plain fact
            metric, `conditionality` for a conditional one, ...). Use the
            `definition` parameter for the extra keys.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            data_model (DataModel | str): data model object or its ID
            name (str): name of the fact metric
            fact (dict, optional): managed fact definition
                (`ms-ManagedFact` schema)
            function (str, optional): aggregation function, e.g. 'sum'
            description (str, optional): description of the fact metric
            definition (dict, optional): additional top-level body keys of the
                `ms-FactMetric` schema merged into the request body (e.g.
                `dimty`, `conditionality`, `functionProperties`)
            show_expression_as (str, optional): specify how expressions are
                presented in the response ('tree' or 'tokens')
            show_advanced_properties (bool, optional): whether to show
                advanced properties in the response
            allow_link (bool, optional): whether to allow linking

        Returns:
            DataModelFactMetric object.
        """
        data_model_id = data_model if isinstance(data_model, str) else data_model.id
        body = {
            'name': name,
            'description': description,
            'fact': fact,
            'function': function,
            **(definition or {}),
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.create_data_model_fact_metric(
            connection,
            id=data_model_id,
            body=body,
            show_expression_as=show_expression_as,
            show_advanced_properties=show_advanced_properties,
            allow_link=allow_link,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created fact metric named: '{name}' with ID: '"
                f"{response.get('id')}' in data model '{data_model_id}'."
            )
        return cls._from_api_source(connection, data_model_id, response)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        fact: dict | None = None,
        function: str | None = None,
        definition: dict | None = None,
    ) -> None:
        """Alter the fact metric (partial update via PATCH).

        Args:
            name (str, optional): new name of the fact metric
            description (str, optional): new description of the fact metric
            fact (dict, optional): new managed fact definition
            function (str, optional): new aggregation function
            definition (dict, optional): additional top-level body keys merged
                into the request body
        """
        body = {
            'name': name,
            'description': description,
            'fact': fact,
            'function': function,
            **(definition or {}),
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.update_data_model_fact_metric(
            self.connection,
            id=self.data_model_id,
            fact_metric_id=self.id,
            body=body,
        )
        self._set_object_attributes(**unpack_information_dict(response.json()))
        if config.verbose:
            logger.info(
                f"Successfully altered fact metric with ID: '{self.id}' in "
                f"data model '{self.data_model_id}'."
            )
