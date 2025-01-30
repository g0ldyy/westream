import sys

from loguru import logger


def setupLogger(level: str):
    logger.level("WESTREAM", no=50, icon="🌠", color="<fg #7871d6>")
    logger.level("API", no=40, icon="👾", color="<fg #7871d6>")

    logger.level("INFO", icon="📰", color="<fg #FC5F39>")
    logger.level("DEBUG", icon="🕸️", color="<fg #DC5F00>")
    logger.level("WARNING", icon="⚠️", color="<fg #DC5F00>")

    log_format = (
        "<white>{time:YYYY-MM-DD}</white> <magenta>{time:HH:mm:ss}</magenta> | "
        "<level>{level.icon}</level> <level>{level}</level> | "
        "<cyan>{module}</cyan>.<cyan>{function}</cyan> - <level>{message}</level>"
    )

    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "level": level,
                "format": log_format,
                "backtrace": False,
                "diagnose": False,
                "enqueue": True,
            }
        ]
    )


setupLogger("DEBUG")
