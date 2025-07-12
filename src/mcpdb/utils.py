import pandas as pd
from sqlalchemy import Engine
from typing import Literal, Callable
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import Connection
from mcpdb.tables import Base

def __postgres_upsert(table: pd.DataFrame, conn: Connection, keys, data_iter):
    data = [dict(zip(keys, row)) for row in data_iter]
    insert_statement = insert(table.table).values(data)
    upsert_statement = insert_statement.on_conflict_do_update(
        constraint=f"PK_{table.table.name}",
        set_={c.key: c for c in insert_statement.excluded},
    )
    result = conn.execute(upsert_statement)
    return result

def __set_data(engine: Engine, table_name: str, data: pd.DataFrame, operation_type: Literal["insert", "append", "upsert"] = "upsert", logging_method: Callable[[str], None] = print):
    """
    Set the data in the PostgreSQL database.
    """
    # Check if the operation type is valid
    if operation_type not in ["insert", "append", "upsert"]:
        raise ValueError(f"Invalid operation type: {operation_type}")

    # Check if the table exists in the tables defined in the mcpdb.tables module
    if table_name not in [table.__tablename__ for table in Base.__subclasses__()]:
        raise ValueError(f"Table {table_name} does not exist in the mcpdb.tables module")

    # Check if the data is a pandas DataFrame
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f"Data is not a pandas DataFrame: {type(data)}")

    # Check if the data is empty
    if data.empty:
        logging_method(f"Data is empty, skipping {table_name}")
        return

    # Insert the data into the database
    if operation_type == "insert":
        logging_method(f"Inserting {len(data)} row(s) to {table_name}")
        data.to_sql(table_name, engine, if_exists='replace',index=False)
    elif operation_type == "append":
        logging_method(f"Appending {len(data)} row(s) to {table_name}")
        data.to_sql(table_name, engine, if_exists='append',index=False) 
    elif operation_type == "upsert":
        logging_method(f"Upserting {len(data)} row(s) to {table_name}")
        data.to_sql(table_name, engine, if_exists='append',index=False, method=__postgres_upsert)

def set_data(engine: Engine, table_name: str, data: pd.DataFrame, operation_type: Literal["insert", "append", "upsert"] = "upsert", logging_method: Callable[[str], None] = print):
    __set_data(engine, table_name, data, operation_type, logging_method)