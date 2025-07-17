import os
import tempfile
import mc_postgres_db.models as models
from sqlalchemy import create_engine
from contextlib import contextmanager
from prefect.blocks.system import Secret
import logging

LOGGER = logging.getLogger(__name__)


@contextmanager
def postgres_test_harness():
    """
    A test harness for testing the PostgreSQL database.
    """
    # Create a temporary file for the SQLite database.
    LOGGER.info("Creating temporary SQLite database file...")
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=True, delete_on_close=False)
    db_path = tmp.name
    LOGGER.info(f"Temporary SQLite database file: {db_path}")

    # Get the engine.
    LOGGER.info("Getting engine for the SQLite database...")
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)

    # Create all models in the database.
    LOGGER.info("Creating all tables in the SQLite database...")
    models.Base.metadata.create_all(engine)

    # Set the postgres-url secret to the URL of the SQLite database.
    Secret(value=url).save("postgres-url", overwrite=True)  # type: ignore

    yield

    # Clean-up the database.
    LOGGER.info("Dropping all tables...")
    models.Base.metadata.drop_all(engine)

    # Close the tempfile.
    LOGGER.info("Closing temporary SQLite database file...")
    tmp.close()

    # Delete the database file.
    LOGGER.info("Deleting temporary SQLite database file...")
    if os.path.exists(db_path):
        os.remove(db_path)
