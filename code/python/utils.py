import logging
import yaml

def read_config(config_file):
    '''
    Reads the configuration yaml file.
    '''
    return yaml.safe_load(open(config_file, 'r'))


def setup_logging():
    '''
    Sets up the logging configuration.
    '''
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )
    log = logging.getLogger(__name__)
    return log