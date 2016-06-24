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

log = logging.getLogger(__name__)

from datetime import date
from tools import loader
from tools import utils


def process(citations_file, output=None, plot=False):
    """

    :param citations_file: list of citations files
    :param output: output file object
    :param plot: whether charts should be plotted
    """
    log.info("Computing citations h-index")
    publication_entries, entries = loader.load_list_of_entries(citations_file)

    # sanity check
    if len(publication_entries) == 0:
        log.error("The citations file has no valid main publication entries.")
        exit(1)

    if len(entries) == 0:
        log.error("The citations file has no valid entries.")
        exit(1)

    # oldest publication year
    minor_year = date.today().year

    for pe in publication_entries:
        if int(pe.year) < minor_year:
            minor_year = int(pe.year)

    # create data analysis structure
    analyzer = Analyzer(minor_year)

    for e in entries:
        analyzer.process(e)

    # write publication entries to output
    h_index = analyzer.get_overall_index()
    for pe in publication_entries:
        pe.h_index = h_index
        utils.write_output(pe, output)

    # write other entries
    for e in entries:
        utils.write_output(e, output)

    if plot:
        # Plot h-index evolution
        if not utils.check_module('pygal'):
            log.error("Unable to generate plot, cannot find module 'pygal'.")
            exit(1)
        pygal = __import__('pygal')

        base_filename = os.path.splitext(citations_file[0])[0]

        config = pygal.Config()
        config.show_legend = False
        chart = pygal.StackedLine(config, fill=True, interpolate='cubic')
        chart.title = "h-index Evolution per Year"
        chart.x_labels = map(str, analyzer.get_years())
        chart.add('h-index', analyzer.get_yearly_indexes())
        chart.render_to_file(base_filename + "-hindex.svg")


class Analyzer:
    def __init__(self, initial_year):
        """

        :param initial_year:
        """
        self.initial_year = initial_year
        self.current_year = date.today().year
        self.all_citations = []
        self.yearly_citations = {}
        for i in range(initial_year, self.current_year + 1):
            self.yearly_citations[i] = []

    def process(self, e):
        """

        :param e: citation entry
        """
        self.all_citations.append(int(e.citations))

        if e.year:
            citation_year = int(e.year)
            if citation_year < self.initial_year:
                citation_year = self.initial_year

            for i in range(citation_year, self.current_year + 1):
                self.yearly_citations[i].append(int(e.citations))

    def get_overall_index(self):
        self.all_citations.sort(reverse=True)
        return self._get_index(self.all_citations)

    def get_years(self):
        values = []
        for year in range(self.initial_year, self.current_year + 1):
            values.append(year)
        return values

    def get_yearly_indexes(self):
        indexes = []

        # sort keys
        all_keys = []
        for key in self.yearly_citations.keys():
            all_keys.append(key)
        all_keys.sort()

        for year in all_keys:
            self.yearly_citations[year].sort(reverse=True)
            indexes.append(self._get_index(self.yearly_citations[year]))

        return indexes

    def _get_index(self, citations_list):
        index = 0
        for i in citations_list:
            index += 1
            if index >= i:
                break
        return index
