"""
    This is a template for creation of Datasource Script.

    Three methods need to be created for the workflow to work:
        browse(): retrieves the catalog information
        preview(): gets partial data for preview, data refine and schema change
        publish(): gets the data published and stores the data into a cube
    All three methods have to return data in the format of Pandas DataFrame.
"""

"""
    Simple Example:
    ```
    import pandas as pd

    # construct 2 tables to import
    year_cost_json = '[{"Year": 2010, "Cost": 7343097.05960049}, ' \\
            '{"Year": 2011, "Cost": 9777520.64980007}, ' \\
            '{"Year": 2012, "Cost": 12609466.8109989}]'
    df_cost = pd.json_normalize(pd.io.json.loads(year_cost_json))
    year_revenue_json = '[{"Year": 2010, "Revenue": 8647238.10000023}, ' \\
            '{"Year": 2011, "Revenue": 11517606}, ' \\
            '{"Year": 2012, "Revenue": 14858864.0500001}]'
    df_revenue = pd.json_normalize(pd.io.json.loads(year_revenue_json))
    all_tables = dict({'YearlyCost': df_cost, 'YearlyRevenue': df_revenue})

    def browse():
        return all_tables

    def preview(table_name, row_count):
        if table_name not in all_tables:
            raise ValueError(f"Table {table_name} is not found.")
        return all_tables.get(table_name).head(row_count)

    def publish(table_name):
        if table_name not in all_tables:
            raise ValueError(f"Table {table_name} is not found.")
        return all_tables.get(table_name)
    ```
"""


def browse():
    """Retrieve the catalog information.

    Returns:
        a dict object. The keys of the dict should be table names of the Python
        data source, and the values are normalized in Pandas DataFrame format.
        Each DataFrame value will contain a table's column infos.
    """
    pass


def preview(table_name, row_count):
    """Get partial data for preview, data refine and schema change.

    Args:
        table_name: name of the selected table.
        row_count: number of rows to be retrieved.

    Returns:
        a Pandas DataFrame object with `row_count` rows.
    """
    pass


def publish(table_name):
    """Get the data published and store the data into the cube

    Args:
        table_name: name of the selected table.

    Returns:
        a Pandas DataFrame object with all data.
    """
    pass
