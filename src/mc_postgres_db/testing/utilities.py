import os
import time
import uuid
import socket
import logging
from contextlib import contextmanager
from urllib.parse import urlparse

import docker
from sqlalchemy import Engine, text, create_engine
from sqlalchemy.exc import OperationalError
from prefect.settings import PREFECT_API_URL
from prefect.blocks.system import Secret
from prefect.testing.utilities import prefect_test_harness

import mc_postgres_db.models as models

LOGGER = logging.getLogger(__name__)

# Test database configuration constants
TEST_DB_USER = "testuser"
TEST_DB_PASSWORD = "testpass"
TEST_DB_NAME = "testdb"
TEST_DB_SIZE_THRESHOLD_MB = 1000


def _validate_test_database_connection(engine: Engine):
    """
    Validate that the database connection is safe for testing.
    Raises ValueError if the connection appears to be to a production database.
    """
    url = engine.url

    # Check driver
    if url.drivername != "postgresql":
        raise ValueError(
            f"Unsupported database driver: {url.drivername}. Only PostgreSQL is supported."
        )

    # Check host is localhost
    if url.host not in ["localhost", "127.0.0.1"]:
        raise ValueError(
            f"PostgreSQL host '{url.host}' is not localhost. "
            "This may be a production database connection!"
        )

    # Check username matches test user
    if url.username != TEST_DB_USER:
        raise ValueError(
            f"PostgreSQL username '{url.username}' is not the expected test user '{TEST_DB_USER}'. "
            "This may be a production database connection!"
        )

    # Check database name matches test database
    if url.database != TEST_DB_NAME:
        raise ValueError(
            f"PostgreSQL database '{url.database}' is not the expected test database '{TEST_DB_NAME}'. "
            "This may be a production database connection!"
        )

    # Additional check: verify we can connect and it's not a production database
    try:
        with engine.connect() as conn:
            # Check database size - if it's too large, it might be production
            result = conn.execute(
                text("""
                SELECT pg_database_size(current_database()) as size_bytes
            """)
            )
            size_bytes = result.fetchone()[0]
            size_mb = size_bytes / (1024 * 1024)

            if (
                size_mb > TEST_DB_SIZE_THRESHOLD_MB
            ):  # More than the threshold might indicate production data
                raise ValueError(
                    f"Database size ({size_mb:.1f}MB) is suspiciously large for a test database. "
                    "This may be a production database!"
                )

    except Exception as e:
        if "production database" in str(e):
            raise
        # If we can't connect or query, that's also suspicious
        raise ValueError(f"Cannot validate database safety: {e}")


def clear_database(engine: Engine):
    """
    Clear the database of all data.
    Performs safety checks to ensure we're not clearing a production database.
    """

    # Validate that this is a safe test database connection
    _validate_test_database_connection(engine)

    # Drop all tables in the database.
    models.Base.metadata.drop_all(engine)

    # Create all tables in the database.
    models.Base.metadata.create_all(engine)


def _find_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def _wait_for_postgres(
    host: str, port: int, user: str, password: str, database: str, timeout: int = 30
):
    """Wait for PostgreSQL to be ready."""
    LOGGER.info(f"Waiting for PostgreSQL to be ready on {host}:{port}...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            test_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            test_engine = create_engine(test_url)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            LOGGER.info("PostgreSQL is ready!")
            return True
        except OperationalError:
            time.sleep(1)

    raise TimeoutError(f"PostgreSQL did not become ready within {timeout} seconds")


@contextmanager
def postgres_test_harness(prefect_server_startup_timeout: int = 30):
    """
    A test harness for testing the PostgreSQL database using Docker.
    """
    # Get PostgreSQL version from environment variable or default to latest
    postgres_version = os.getenv("POSTGRES_VERSION", "latest")

    # Use ephemeral storage for PostgreSQL data (no volume mounting)
    LOGGER.info("Using ephemeral storage for PostgreSQL data (no volume mounting)")

    # Generate unique container name
    container_name = f"test-postgres-{uuid.uuid4().hex[:8]}"

    # Database configuration
    db_user = TEST_DB_USER
    db_password = TEST_DB_PASSWORD
    db_name = TEST_DB_NAME

    # Find a free port
    port = _find_free_port()
    LOGGER.info(f"Using port {port} for PostgreSQL container")

    # Initialize Docker client
    try:
        client = docker.from_env()
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize Docker client: {e}\n"
            "Please ensure Docker is running. You can start Docker Desktop or run:\n"
            "  docker --version  # to check if Docker is installed\n"
            "  docker ps         # to check if Docker daemon is running\n"
            "If Docker is not available, you may need to install Docker Desktop or start the Docker daemon."
        )

    container = None
    try:
        # Start PostgreSQL container
        LOGGER.info(
            f"Starting PostgreSQL container '{container_name}' with image postgres:{postgres_version}..."
        )

        # Start PostgreSQL container with ephemeral storage
        container = client.containers.run(
            f"postgres:{postgres_version}",
            name=container_name,
            environment={
                "POSTGRES_USER": db_user,
                "POSTGRES_PASSWORD": db_password,
                "POSTGRES_DB": db_name,
            },
            ports={5432: port},
            detach=True,
            remove=False,  # We'll remove manually for better control
        )

        # Wait for PostgreSQL to be ready
        _wait_for_postgres("localhost", port, db_user, db_password, db_name)

        # Additional safety check: verify the container is actually running our test instance
        LOGGER.info("Verifying container is our test instance...")
        try:
            container_info = container.attrs
            container_env = container_info.get("Config", {}).get("Env", [])

            # Check that our environment variables are set in the container
            env_dict = {}
            for env_var in container_env:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    env_dict[key] = value

            if env_dict.get("POSTGRES_USER") != db_user:
                raise ValueError(
                    f"Container POSTGRES_USER mismatch: expected {db_user}, got {env_dict.get('POSTGRES_USER')}"
                )
            if env_dict.get("POSTGRES_DB") != db_name:
                raise ValueError(
                    f"Container POSTGRES_DB mismatch: expected {db_name}, got {env_dict.get('POSTGRES_DB')}"
                )

            LOGGER.info("Container verification passed - confirmed test instance")
        except Exception as e:
            raise ValueError(f"Failed to verify container safety: {e}")

        # Create database URL and engine
        database_url = (
            f"postgresql://{db_user}:{db_password}@localhost:{port}/{db_name}"
        )
        LOGGER.info(
            f"Database URL: postgresql://{db_user}:***@localhost:{port}/{db_name}"
        )
        engine = create_engine(database_url)

        # Comprehensive validation that this is a safe test database
        LOGGER.info("Validating database connection safety...")
        _validate_test_database_connection(engine)
        LOGGER.info("Database connection validation passed - safe for testing")

        # Create all models in the database
        LOGGER.info("Creating all tables in the PostgreSQL database...")
        models.Base.metadata.create_all(engine)

        # Initialize the Prefect test harness
        with prefect_test_harness(
            server_startup_timeout=prefect_server_startup_timeout
        ):
            # Check if the PREFECT_API_URL environment variable is set to localhost
            prefect_api_url = urlparse(PREFECT_API_URL.value())
            print(f"URL hostname: {prefect_api_url.hostname}")
            print(f"URL port: {prefect_api_url.port}")
            print(f"URL netloc: {prefect_api_url.netloc}")
            valid_hostnames = ["localhost", "127.0.0.1"]
            if prefect_api_url.hostname not in valid_hostnames:
                raise ValueError(
                    "The PREFECT_API_URL environment variable has it's hostname set to something other than localhost"
                )

            # Set the postgres-url secret to the URL of the PostgreSQL database
            Secret(value=database_url).save("postgres-url")  # type: ignore

            # Check if the secret is set
            postgres_url_secret = Secret.load("postgres-url").get()
            if postgres_url_secret is None or postgres_url_secret == "":
                raise ValueError("The postgres-url secret is not set.")

            # Check if the secret is the same as the database URL
            if postgres_url_secret != database_url:
                raise ValueError(
                    "The postgres-url secret is not the same as the database URL."
                )

            yield

    finally:
        # Clean-up the database
        if container:
            try:
                LOGGER.info("Dropping all tables...")
                models.Base.metadata.drop_all(engine)
            except Exception as e:
                LOGGER.warning(f"Error dropping tables: {e}")

            # Stop and remove container
            try:
                LOGGER.info(f"Stopping PostgreSQL container '{container_name}'...")
                container.stop(timeout=10)
                LOGGER.info(f"Removing PostgreSQL container '{container_name}'...")
                container.remove()
            except Exception as e:
                LOGGER.warning(f"Error cleaning up container: {e}")

        # No temporary directory cleanup needed with ephemeral storage
