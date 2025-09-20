import logging
import os
import tempfile
from contextlib import contextmanager

from prefect.blocks.system import Secret
from prefect.testing.utilities import prefect_test_harness
from prefect.settings import PREFECT_API_URL
from sqlalchemy import Engine, create_engine
from urllib.parse import urlparse

import mc_postgres_db.models as models

LOGGER = logging.getLogger(__name__)


def clear_database(engine: Engine):
    """
    Clear the database of all data.
    """

    # Check if the engine is a SQLite engine.
    if engine.url.drivername != "sqlite":
        raise ValueError("The engine is not a SQLite engine.")

    # Check if the database file exists.
    if not os.path.exists(engine.url.database):
        raise ValueError(f"The database file {engine.url.database} does not exist.")

    # Drop all tables in the database.
    models.Base.metadata.drop_all(engine)

    # Create all tables in the database.
    models.Base.metadata.create_all(engine)


@contextmanager
def postgres_test_harness(prefect_server_startup_timeout: int = 30):
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
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url)

    # Throw an error if the engine is not a SQLite engine.
    if engine.url.drivername != "sqlite":
        raise ValueError("The engine is not a SQLite engine.")

    # Create all models in the database.
    LOGGER.info("Creating all tables in the SQLite database...")
    models.Base.metadata.create_all(engine)

    # Initialize the Prefect test harness as well to ensure that we have the proper environment setup.
    with prefect_test_harness(server_startup_timeout=prefect_server_startup_timeout):
        # Check if the PREFECT_API_URL environment variable is set to localhost (on any port). Throw an error if it is not.
        prefect_api_url = urlparse(PREFECT_API_URL.value())
        print(f"URL hostname: {prefect_api_url.hostname}")
        print(f"URL port: {prefect_api_url.port}")
        print(f"URL netloc: {prefect_api_url.netloc}")
        valid_hostnames = ["localhost", "127.0.0.1"]
        if prefect_api_url.hostname not in valid_hostnames:
            raise ValueError(
                "The PREFECT_API_URL environment variable has it's hostname set to something other than localhost"
            )

        # Set the postgres-url secret to the URL of the SQLite database.
        Secret(value=database_url).save("postgres-url")  # type: ignore

        # Check if the secret is set.
        postgres_url_secret = Secret.load("postgres-url").get()
        if postgres_url_secret is None or postgres_url_secret == "":
            raise ValueError("The postgres-url secret is not set.")

        # Check if the secret is the same as the database URL.
        if postgres_url_secret != database_url:
            raise ValueError(
                "The postgres-url secret is not the same as the database URL."
            )

        yield

    # Throw an error if the engine is not a SQLite engine.
    if engine.url.drivername != "sqlite":
        raise ValueError("The engine is not a SQLite engine.")

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
