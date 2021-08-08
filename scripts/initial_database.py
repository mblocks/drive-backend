import logging
import app.db.models  # noqa: F401
from app.db.base_class import Base
from app.db.session import engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Initial database tables created")


if __name__ == "__main__":
    main()
