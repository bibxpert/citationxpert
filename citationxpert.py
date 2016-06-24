#!/usr/bin/env python
#
# Copyright 2016 Rafael Ferreira da Silva
# http://www.rafaelsilva.com/tools
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

import logging
import sys

from optparse import OptionParser, OptionGroup
from operations import author
from operations import author_map
from operations import citations
from operations import h_index
from operations import self_reference
from tools import utils

log = logging.getLogger(__name__)

VERSION = "1.0.0-dev"
ANALYSIS_OPTIONS = ['self', 'h-index', 'author']


def option_parser(usage):
    """
    Parse the command line options.
    :param usage: tool usage string
    :return: parsed options and arguments
    """
    parser = OptionParser(usage="usage: %s" % usage, version=VERSION,
                          description="CitationXpert: an open-source citation analysis tool based on Google Scholar",
                          epilog="Documentation and releases are available at: "
                                 "http://www.rafaelsilva.com/tools/citationxpert")

    parser.add_option("-c", "--citations", dest="publication_title", action="store", type="string",
                      default=None, help="Get all citations for the publication")
    parser.add_option("-a", "--analysis", dest="analysis_type", action="store",
                      help="Available analyses: %s" % ANALYSIS_OPTIONS)
    parser.add_option("-i", "--input", dest="citations_file", action="append",
                      help="Citations file generated by '-c' option.")
    parser.add_option("-p", "--plot", dest="plot", action="store_true",
                      default=False, help="Plot graph(s).")
    parser.add_option("-m", "--authors-map", dest="authors_file", action="store",
                      help="Create a map of authors from an authors file (generated using '-a author')")

    parser.add_option("-o", "--output", action="store", type="string",
                      dest="output", default=None, help="Output file")

    logging_group = OptionGroup(parser, "Logging Options")
    logging_group.add_option("-d", "--debug", dest="debug", action="store_true",
                             default=False, help="Turn on debugging")
    logging_group.add_option("-v", "--verbose", dest="verbose", action="store_true",
                             default=False, help="Show progress messages")
    parser.add_option_group(logging_group)

    fn = parser.parse_args

    def parse(*args, **kwargs):
        options, args = fn(*args, **kwargs)

        if options.debug:
            utils.configure_logging(level=logging.DEBUG)
        elif options.verbose:
            utils.configure_logging(level=logging.INFO)
        else:
            utils.configure_logging(logging.WARNING)
        return options, args

    parser.parse_args = parse

    return parser


def main():
    args = sys.argv[1:]
    parser = option_parser("citationxpert [OPTIONS]")
    options, args = parser.parse_args(args)

    if options.output:
        output_file = open(options.output, 'w')
        log.info("Writing entries to '%s'." % options.output)
    else:
        output_file = None

    if options.publication_title:
        # Get citations
        citations.process(options.publication_title, output=output_file)

    elif options.analysis_type:
        # Overall citation analysis
        if options.analysis_type not in ANALYSIS_OPTIONS:
            log.error("The provided analysis type is not supported: %s" % options.analysis_type)
            exit(1)
        if not options.citations_file:
            log.error("A file with all citations should be provided.")
            exit(1)
        if options.analysis_type == 'self':
            self_reference.process(options.citations_file, output=output_file, plot=options.plot)
        elif options.analysis_type == 'author':
            author.process(options.citations_file, output=output_file, plot=options.plot)
        elif options.analysis_type == 'h-index':
            h_index.process(options.citations_file, output=output_file, plot=options.plot)

    elif options.authors_file:
        # Create authors map
        author_map.process(options.authors_file, output=output_file)

    else:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    main()