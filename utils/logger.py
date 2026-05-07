"""Logger services for writing to terminal and log files."""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("     mongoLogger")
rlogger = logging.getLogger("     redisLogger")
slogger = logging.getLogger("     serverLogger")
tlogger = logging.getLogger("     MQTTLogger")
xlogger = logging.getLogger("     schedulerLogger")
