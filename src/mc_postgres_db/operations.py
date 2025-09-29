from typing import Literal, Callable

import pandas as pd
from sqlalchemy import Engine, Connection
from sqlalchemy.dialects.postgresql import insert

from mc_postgres_db.models import Base


def __upsert(table: pd.DataFrame, conn: Connection, keys, data_iter):
    """
    Upsert the data into the database using the SQLAlchemy upsert statement. This is a custom SQLAlchemy method that will be used in the pd.to_sql method.
    """
    data = [dict(zip(keys, row)) for row in data_iter]
    insert_statement = insert(table.table).values(data)
    upsert_statement = insert_statement.on_conflict_do_update(
        constraint=f"{table.table.name}_pkey",
        set_={c.key: c for c in insert_statement.excluded},
    )
    result = conn.execute(upsert_statement)
    return result


def __set_data(
    engine: Engine,
    table_name: str,
    data: pd.DataFrame,
    operation_type: Literal["append", "upsert"] = "upsert",
    logging_method: Callable[[str], None] = print,
):
    """
    Set the data in the PostgreSQL database. This is the base method that we will re-use for other methods and Prefect tasks where the logging method will vary.
    """
    # Check if the operation type is valid
    if operation_type not in ["append", "upsert"]:
        raise ValueError(f"Invalid operation type: {operation_type}")

    # Check if the table exists in the tables defined in the mcpdb.tables module
    if table_name not in [table.__tablename__ for table in Base.__subclasses__()]:
        raise ValueError(
            f"Table {table_name} does not exist in the mcpdb.tables module"
        )

    # Check if the data is a pandas DataFrame
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f"Data is not a pandas DataFrame: {type(data)}")

    # Check if the data is empty
    if data.empty:
        logging_method(f"Data is empty, skipping {table_name}")
        return

    # Insert the data into the database
    if operation_type == "append":
        logging_method(f"Appending {len(data)} row(s) to {table_name}")
        data.to_sql(table_name, engine, if_exists="append", index=False)
    elif operation_type == "upsert":
        logging_method(f"Upserting {len(data)} row(s) to {table_name}")
        data.to_sql(
            table_name,
            engine,
            if_exists="append",
            index=False,
            method=__upsert,
        )


def set_data(
    engine: Engine,
    table_name: str,
    data: pd.DataFrame,
    operation_type: Literal["append", "upsert"] = "upsert",
):
    """
    Set the data in the PostgreSQL database, logging the operation to the console.
    """
    __set_data(engine, table_name, data, operation_type, logging_method=print)
