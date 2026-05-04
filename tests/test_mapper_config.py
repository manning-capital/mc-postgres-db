import os
import sys
import warnings

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import configure_mappers

import mc_postgres_db.models  # noqa: F401  (imported for side-effect: registers mappers)


def test_configure_mappers_emits_no_sawarning():
    with warnings.catch_warnings():
        warnings.simplefilter("error", SAWarning)
        configure_mappers()
