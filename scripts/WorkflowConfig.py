__author__ = 'dan'
import os, sys, ConfigParser
from collections import defaultdict

def parseProjectConfig(file):

    sys.stdout.write("Parsing configuration file %s\n" % file)

    config = _parseConfig(file)

    sections = config.sections()

    configuration = dict()
    configuration['version'] = config.get('information', 'version')
    configuration['clean'] = config.getboolean('information', 'clean_intermediates')

    try:
        configuration['dir'] = config.get('information', 'project_directory')
    except:
        configuration['dir'] = None

    try:
        configuration['assembly_dir'] = config.get('information', 'assembly_directory')
    except:
        configuration['assembly_dir'] = None

    try:
        configuration['num_cores'] = config.getint('information', 'num_cores')
    except:
        configuration['num_cores'] = 1

    try:
        configuration['project_name'] = config.getint('information', 'project_name')
    except:
        configuration['project_name'] = 'samples'

    #Check if workflow is production or development to set tool_folder directory
    try:
        configuration['production'] = config.getboolean('information', 'production')
        TOOL_CONFIG_DIR = os.path.join(basedir, 'app/workflows/tools/production/')
        sys.stdout.write("Set tool configuration and executables directory to %s\n" % TOOL_CONFIG_DIR)
        logging.info("Set tool configuration and executables directory to %s\n" % TOOL_CONFIG_DIR)
    except:
        configuration['production'] = False

    try:
        configuration['development'] = config.getboolean('information', 'development')
        TOOL_CONFIG_DIR = os.path.join(basedir, 'app/workflows/tools/development/')
        sys.stdout.write("Set tool configuration and executables directory to %s\n" % TOOL_CONFIG_DIR)
        logging.info("Set tool configuration and executables directory to %s\n" % TOOL_CONFIG_DIR)
    except:
        configuration['development'] = False

    sample_ids = [x.strip() for x in config.get('information', 'samples').split(',')]
    samples = []
    for sample in sample_ids:
        options = config.options(sample)
        sample_dict = defaultdict()
        sample_dict['name'] = sample
        for option in options:
            sample_dict[option] = config.get(sample, option)
        samples.append(sample_dict)
    configuration['samples'] = samples

    if 'resources' in sections:
        #Override tool-level defined resources with project-level configurations
        for resource in config.options('resources'):
            configuration[resource] = config.get('resources', resource)

    return configuration

def _parseConfig(file):
    #logging.debug("Reading Config from: %s\n" % file)
    config = ConfigParser.SafeConfigParser()
    config.read(file)

    return config