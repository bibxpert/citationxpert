#!/usr/bin/env python
#
#  Copyright 2016 Rafael Ferreira da Silva
#  http://www.rafaelsilva.com/tools
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
__author__ = "Rafael Ferreira da Silva"

import imp
import logging
import sys
from difflib import SequenceMatcher

log = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.9


class ConsoleHandler(logging.StreamHandler):
    """A handler that logs to console in the sensible way.

    StreamHandler can log to *one of* sys.stdout or sys.stderr.

    It is more sensible to log to sys.stdout by default with only error
    (logging.ERROR and above) messages going to sys.stderr. This is how
    ConsoleHandler behaves.
    """

    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.stream = None  # reset it; we are not going to use it anyway

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.__emit(record, sys.stderr)
        else:
            self.__emit(record, sys.stdout)

    def __emit(self, record, strm):
        self.stream = strm
        logging.StreamHandler.emit(self, record)

    def flush(self):
        # Workaround a bug in logging module
        # See:
        #   http://bugs.python.org/issue6333
        if self.stream and hasattr(self.stream, 'flush') and not self.stream.closed:
            logging.StreamHandler.flush(self)


def configure_logging(level=logging.INFO):
    """
    Initialize log properties, level, and format.
    :param level: logging level
    """
    root = logging.getLogger()
    root.setLevel(level)
    cl = ConsoleHandler()
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s(%(lineno)d): %(message)s")
    cl.setFormatter(formatter)
    root.addHandler(cl)


def write_output(value, output=None):
    """
    Write output value to file (defined by output) or standard output stream.
    :param value: value object to be written
    :param output: output file object
    """
    if output:
        output.write(str(value))
    else:
        print value


def check_module(module_name):
    """
    Verify if a module exists
    :param module_name: name of the module
    :return: whether the module exists
    """
    try:
        imp.find_module(module_name)
        return True
    except ImportError:
        return False


def parse_country_code(country_code):
    """
    Parse country code from URL to determine origin.
    :param country_code: country code from URL
    :return: parsed country code
    """
    cc = str(country_code).lower()
    if cc.lower() == 'edu' or cc.lower() == 'com' or cc.lower() == 'org' or cc.lower() == 'gov':
        return 'us'
    if cc.lower() == 'uk':
        return 'gb'
    return cc


def is_similar(a, b, threshold=SIMILARITY_THRESHOLD):
    """
    Compare if two strings are similar.
    :param a: first string
    :param b: second string
    :param threshold: similarity threshold
    :return: whether two strings are similar
    """
    ratio = SequenceMatcher(None, a, b).ratio()
    if ratio >= threshold:
        log.debug("String similarity of '%s' detected between: '%s' AND '%s'" % (ratio, a, b))
        return True
    return False
