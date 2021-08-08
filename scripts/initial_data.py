import logging
from app.db.session import SessionLocal
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Creating initial data")
    init_db(SessionLocal())
    logger.info("Initial data created")

if __name__ == "__main__":
    main()


