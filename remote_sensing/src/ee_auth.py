"""Earth Engine session bootstrap."""
import os

import ee
from dotenv import load_dotenv


def init_ee() -> None:
    load_dotenv()
    project = os.environ.get("EE_PROJECT")
    if not project or project == "your-gcp-project-id":
        raise RuntimeError(
            "Set EE_PROJECT in .env to your Earth Engine-enabled GCP project id "
            "(copy .env.example to .env first)."
        )
    try:
        ee.Initialize(project=project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)
