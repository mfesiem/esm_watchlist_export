# -*- coding: utf-8 -*-

import os
import configparser
from collections import UserDict
from configparser import NoSectionError, NoOptionError

class ESMConfig(UserDict):
    """A class to find and contain ESM creds and config."""

    def __init__(self, path=None, esm='esm', *args):
        """
        Initializes the ESMConfig. 
        
        Credentials for the ESM(s) live in an .ini file that should be
        located in a user directory with properly restrictive permissions.

        This class will check for environemental variables for a home dir
        and check there and then check in the local dir.

        Args:
            path (str): path to a mfesaw ini file. 

            esm (str): section name of the esm settings in the ini file.
                        default is 'default'.
        """
        self.data = {}
        config = configparser.ConfigParser()

        if path:
            config.read(path)
        else:
            home_vars = ['HOME', 'APPDATA', 'XDG_HOME']
            ini_paths = _find_envs(home_vars)
            ini_paths.append('.')
            ini_names = ['.mfe_saw.ini', '.mfesaw.ini', '.mfesaw2.ini']
            ini_files = _find_files(ini_names, ini_paths)
            config.read(ini_files)

        if not config:
            raise FileNotFoundError('.mfesaw2.ini file not found.')

        if not config.has_section(esm):
            raise NoSectionError('Section not found in INI file: {}'
                                    .format(esm))
        
        options = ['esmhost', 'esmuser', 'esmpass']
        for opt in options:
            if not config.has_option(esm, opt):
                raise NoOptionError('Missing opt in ini file.'.format(opt))
            self.__dict__[opt] = config[esm][opt]
            self[opt] = config[esm][opt]
            
def _find_envs(env_vars):
    """Searches env for given variables.
    Args:
        vars (str, list): variable(s) to be checked.

    Returns: list of values for any variables found.
    """
    if isinstance(env_vars, str):
        env_vars = [env_vars]            
    return [val for var, val in os.environ.items() if var in env_vars]

def _find_files(files, paths):
    """Detect ini files in a list of given paths.
    Args:
        files (list): list of filenames to search.
        paths (list): list of paths to search for the list of files.

    Returns:
        List of file paths verified to exist from given files/paths.
    """
    found_files = []           
    for path in paths:
        for file in files:
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                found_files.append(file_path)
    return found_files