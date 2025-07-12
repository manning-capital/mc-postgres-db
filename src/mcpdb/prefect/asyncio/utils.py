from prefect import task
from prefect.blocks.system import Secret
from sqlalchemy import Engine, create_engine
from prefect import get_run_logger
import pandas as pd
from typing import Literal
from mcpdb.utils import __set_data

@task()
async def get_postgres_url(
    password_secret_block_name: str,
    host_secret_block_name: str,
    port_secret_block_name: str,
    database_secret_block_name: str,
    user_secret_block_name: str,
) -> str:
    """
    Get the PostgreSQL connection string from a secret block.
    """
    postgresql_password: str = (await Secret.load(password_secret_block_name)).get()  # type: ignore
    host = (await Secret.load(host_secret_block_name)).get()  # type: ignore
    port = (await Secret.load(port_secret_block_name)).get()  # type: ignore
    database = (await Secret.load(database_secret_block_name)).get()  # type: ignore
    user = (await Secret.load(user_secret_block_name)).get()  # type: ignore
    url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
        user=user,
        password=postgresql_password,
        host=host,
        port=port,
        database=database,
    )
    return url

@task()
async def get_engine(postgres_url: str) -> Engine:
    """
    Get the PostgreSQL engine from the connection string.
    """
    return create_engine(postgres_url)

@task()
async def set_data(engine: Engine, table_name: str, data: pd.DataFrame, operation_type: Literal["insert", "append", "upsert"] = "upsert"):
    """
    Set the data in the PostgreSQL database.
    """
    logger = get_run_logger()
    __set_data(engine, table_name, data, operation_type, logging_method=logger.info)
