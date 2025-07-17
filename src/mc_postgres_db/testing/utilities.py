import os
import tempfile
import mc_postgres_db.models as models
from prefect import task
from sqlalchemy import create_engine, Engine
from contextlib import contextmanager
from unittest.mock import patch
import logging

LOGGER = logging.getLogger(__name__)


def __mock_get_engine(db_path: str):
    """
    Get the engine for the PostgreSQL database. This is a mock engine that uses an in-memory SQLite database.
    """
    return create_engine(f"sqlite:///{db_path}")


@contextmanager
def postgres_test_harness():
    """
    A test harness for testing the PostgreSQL database.
    """
    # Create a temporary file for the SQLite database.
    LOGGER.info("Creating temporary SQLite database file...")
    tmp = tempfile.NamedTemporaryFile(suffix=".db")
    db_path = tmp.name
    LOGGER.info(f"Temporary SQLite database file: {db_path}")

    # Get the engine.
    LOGGER.info("Getting engine for the SQLite database...")
    engine = __mock_get_engine(db_path)

    # Create all models in the database.
    LOGGER.info("Creating all tables in the SQLite database...")
    models.Base.metadata.create_all(engine)

    # Create a task that returns the engine for the PostgreSQL database.
    @task()
    def mock_get_engine_task() -> Engine:
        """
        A task that returns the engine for the PostgreSQL database.
        """
        return __mock_get_engine(db_path)

    # Create a task that returns the engine for the PostgreSQL database.
    @task()
    async def mock_get_engine_task_async() -> Engine:
        """
        A task that returns the engine for the PostgreSQL database.
        """
        return __mock_get_engine(db_path)

    # Patch the get_engine function to return the mock engine.
    with (
        patch("mc_postgres_db.prefect.tasks.get_engine", mock_get_engine_task),
        patch(
            "mc_postgres_db.prefect.asyncio.tasks.get_engine",
            mock_get_engine_task_async,
        ),
    ):
        yield

    # Clean-up the database.
    LOGGER.info("Dropping all tables...")
    models.Base.metadata.drop_all(engine)

    # Close the tempfile.
    LOGGER.info("Closing temporary SQLite database file...")
    tmp.close()

    # Delete the database file.
    LOGGER.info("Deleting temporary SQLite database file...")
    os.unlink(db_path)
