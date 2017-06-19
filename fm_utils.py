import os, sys
import logging

from rftool.utils import file_utils

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def get_projects(path, mode='server'): 
	if mode == 'server': 
		return file_utils.listFolder(path)
