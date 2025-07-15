import os
import logging
from datetime import timedelta

from wl_config_manager import ConfigManager

cm=ConfigManager ("./config.yaml",log_level=logging.ERROR)
config=cm.temuragi
