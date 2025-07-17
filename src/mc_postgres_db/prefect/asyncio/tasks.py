from prefect import task
from prefect.blocks.system import Secret
from sqlalchemy import Engine, create_engine
from prefect import get_run_logger
import pandas as pd
from typing import Literal
from mc_postgres_db.operations import __set_data


@task()
async def get_engine() -> Engine:
    """
    Get the PostgreSQL engine from the connection string.
    """
    postgresql_password: str = (await Secret.load("postgres-password")).get()  # type: ignore
    host = (await Secret.load("postgres-host")).get()  # type: ignore
    port = (await Secret.load("postgres-port")).get()  # type: ignore
    database = (await Secret.load("postgres-database")).get()  # type: ignore
    user = (await Secret.load("postgres-user")).get()  # type: ignore
    url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
        user=user,
        password=postgresql_password,
        host=host,
        port=port,
        database=database,
    )
    return create_engine(url)


@task()
async def set_data(
    table_name: str,
    data: pd.DataFrame,
    operation_type: Literal["append", "upsert"] = "upsert",
):
    """
    Set the data in the PostgreSQL database.
    """
    logger = get_run_logger()
    engine = await get_engine()
    __set_data(engine, table_name, data, operation_type, logging_method=logger.info)
