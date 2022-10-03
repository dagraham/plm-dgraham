#tp!/usr/bin/env python3
import sys
import os
import logging
import logging.config
logging.getLogger('asyncio').setLevel(logging.WARNING)
logger = logging.getLogger()
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.styles.named_colors import NAMED_COLORS
from copy import deepcopy

import ruamel.yaml
yaml = ruamel.yaml.YAML()

def setup_logging(level, homedir, file=None):
    """
    Setup logging configuration. Override root:level in
    logging.yaml with default_level.
    """

    if not os.path.isdir(homedir):
        return

    log_levels = {
        1: logging.DEBUG,
        2: logging.INFO,
        3: logging.WARN,
        4: logging.ERROR,
        5: logging.CRITICAL
    }

    level = int(level)
    loglevel = log_levels.get(level, log_levels[3])

    # if we get here, we have an existing homedir
    logfile = os.path.normpath(os.path.abspath(os.path.join(homedir, "plm.log")))

    config = {'disable_existing_loggers': False,
              'formatters': {'simple': {
                  'format': '--- %(asctime)s - %(levelname)s - %(module)s.%(funcName)s\n    %(message)s'}},
              'handlers': {
                    'file': {
                        'backupCount': 7,
                        'class': 'logging.handlers.TimedRotatingFileHandler',
                        'encoding': 'utf8',
                        'filename': logfile,
                        'formatter': 'simple',
                        'level': loglevel,
                        'when': 'midnight',
                        'interval': 1}
              },
              'loggers': {
                  'etmmv': {
                    'handlers': ['file'],
                    'level': loglevel,
                    'propagate': False}
              },
              'root': {
                  'handlers': ['file'],
                  'level': loglevel},
              'version': 1}
    logging.config.dictConfig(config)
    logger.critical("\n######## Initializing logging #########")
    if file:
        logger.critical(f'logging for file: {file}\n    logging at level: {loglevel}\n    logging to file: {logfile}')
    else:
        logger.critical(f'logging at level: {loglevel}\n    logging to file: {logfile}')


def main():
    import plm
    import plm.__version__ as version
    plm_version = version.version

    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logger = logging.getLogger()
    MIN_PYTHON = (3, 7, 3)
    if sys.version_info < MIN_PYTHON:
        mv = ".".join([str(x) for x in MIN_PYTHON])
        sys.exit(f"Python {mv} or later is required.\n")
    import os
    IS_VENV = os.getenv('VIRTUAL_ENV') is not None
    import plm.__version__ as version

    cwd = os.getcwd()
    dlst = [x for x in os.listdir(cwd) if not x.startswith('.')]
    plmHOME = os.environ.get("plmHOME")
    if len(dlst) == 0 or ('projects' in dlst and 'roster.yaml' in dlst):
        # use cwd if it is empty or contains both data and logs
        plmhome = cwd
    elif plmHOME and os.path.isdir(plmHOME):
        # else use plmHOME if it is set and specifies a directory
        plmhome = plmHOME
    else:
        # use the default ~/plm
        plmhome = os.path.join(os.path.expanduser('~'), 'plm')
        if not os.path.isdir(plmhome):
            text = prompt(f"'{plmhome}' does not exist. Create it [yN] > ")
            if text.lower().strip() == 'y':
                os.mkdir(plmhome)
            else:
                print("cancelled")
                return

    logdir = os.path.normpath(os.path.join(plmhome, 'logs'))
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    loglevel = 2 # info
    log_levels = [str(x) for x in range(1, 6)]
    if len(sys.argv) > 1 and sys.argv[1] in log_levels:
        loglevel = int(sys.argv.pop(1))

    setup_logging(loglevel, logdir)
    logger.debug(f"plm home directory: '{plmhome}'")
    roster = os.path.join(plmhome, 'roster.yaml')
    if not os.path.isfile(roster):
        with open(roster, 'w') as fo:
            fo.write("""\
# plm roster file - each player line should have the format:
# lastname, firstname: [emailaddress, tag1, tag2, ...]
""")
        logger.info(f"Created '{roster}'")


    projects = os.path.join(plmhome, 'projects')
    if not os.path.isdir(projects):
        os.makedirs(projects)
        logger.info(f"Created '{projects}'")

    import plm.plm as plm
    plm.logger = logger
    plm.plm_version = plm_version
    plm.plm_projects = projects
    plm.plm_roster = roster
    plm.plm_home = os.path.join('~', os.path.relpath(plmhome, os.path.expanduser('~')))

    plm.main()

