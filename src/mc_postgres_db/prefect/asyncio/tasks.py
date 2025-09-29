from typing import Literal

import pandas as pd
from prefect import task, get_run_logger
from sqlalchemy import Engine, create_engine
from prefect.blocks.system import Secret

from mc_postgres_db.operations import __set_data


@task()
async def get_engine() -> Engine:
    """
    Get the PostgreSQL engine from the connection string.
    """
    postgres_url = (await Secret.load("postgres-url")).get()  # type: ignore
    return create_engine(postgres_url)


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
