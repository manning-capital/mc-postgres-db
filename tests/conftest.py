import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import pytest
from mc_postgres_db.testing.utilities import postgres_test_harness


@pytest.fixture(scope="session", autouse=True)
def postgres_harness():
    with postgres_test_harness(prefect_server_startup_timeout=45):
        yield
