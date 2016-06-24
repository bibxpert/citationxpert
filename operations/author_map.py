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
import os

from tools import loader
from tools import utils

log = logging.getLogger(__name__)


def process(authors_file, output=None):
    """

    :param authors_file:
    :param output:
    """
    log.info("Plotting Authors Map")

    if not utils.check_module('pygal'):
        log.error("Unable to generate plot, cannot find module 'pygal'.")
        exit(1)
    pygal = __import__('pygal')

    authors_list = loader.load_authors(authors_file)

    # remove duplicated entries
    authors = []
    for author in authors_list:
        if author not in authors:
            authors.append(author)

    log.info("Creating authors map for %s authors." % len(authors))

    # build countries count map
    countries_count = {}
    for author in authors:
        if output:
            utils.write_output(author.print_as_entry(), output)
        if not author.country_code:
            continue
        if author.country_code in countries_count.keys():
            countries_count[author.country_code] += 1
        else:
            countries_count[author.country_code] = 1

    base_filename = os.path.splitext(authors_file)[0]

    config = pygal.Config()
    config.show_legend = False
    chart = pygal.maps.world.World(config)
    chart.title = 'Authors per Country'
    chart.add('Authors', countries_count)
    chart.render_to_file(base_filename + "-authorsmap.svg")
