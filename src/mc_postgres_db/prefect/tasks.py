from prefect import task, get_run_logger
from prefect.blocks.system import Secret
from sqlalchemy import Engine, create_engine
import pandas as pd
from typing import Literal
from mc_postgres_db.operations import __set_data


@task()
def get_engine() -> Engine:
    """
    Get the PostgreSQL engine from the connection string.
    """
    postgresql_password: str = Secret.load("postgres-password").get()  # type: ignore
    host = Secret.load("postgres-host").get()  # type: ignore
    port = Secret.load("postgres-port").get()  # type: ignore
    database = Secret.load("postgres-database").get()  # type: ignore
    user = Secret.load("postgres-user").get()  # type: ignore
    url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
        user=user,
        password=postgresql_password,
        host=host,
        port=port,
        database=database,
    )
    return create_engine(url)


@task()
def set_data(
    table_name: str,
    data: pd.DataFrame,
    operation_type: Literal["append", "upsert"] = "upsert",
):
    """
    Set the data in the PostgreSQL database.
    """
    logger = get_run_logger()
    engine = get_engine()
    __set_data(engine, table_name, data, operation_type, logging_method=logger.info)
