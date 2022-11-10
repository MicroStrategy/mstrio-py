"""
    This is a template for creation of Datasource Script.

    Three methods need to be created for the workflow to work:
        browse(): retrieves the catalog information
        preview(): gets partial data for preview, data refine and schema change
        publish(): gets the data published and stores the data into a cube

    Simple Example:
    ```
    all_tables = /some method to gather required tables/

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
    pass


def preview(table_name, row_count):
    pass


def publish(table_name):
    pass
