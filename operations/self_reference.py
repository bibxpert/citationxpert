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

from datetime import date
from operations import entry
from tools import loader
from tools import utils

log = logging.getLogger(__name__)


def process(citations_file, output=None, plot=False):
    """
    Process the citations to verify whether they self-reference.
    :param citations_file: list of citations files
    :param output: output file object
    :param plot: whether charts should be plotted
    """
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

    # list of publication authors
    publication_authors = entry.Authors()

    # write publication entries to output
    for pe in publication_entries:
        utils.write_output(pe, output)
        publication_authors.authors.extend(pe.authors.authors)
        if int(pe.year) < minor_year:
            minor_year = int(pe.year)

    # create data analysis structure
    analyzer = Analyzer(minor_year)

    for e in entries:
        e.op_self = e.authors.has_authors(publication_authors)
        analyzer.process_entry(e)
        utils.write_output(e, output)

    if plot:
        # Plot all files from the analyses
        if not utils.check_module('pygal'):
            log.error("Unable to generate plot, cannot find module 'pygal'.")
            exit(1)
        pygal = __import__('pygal')

        base_filename = os.path.splitext(citations_file[0])[0]

        # Overall references
        chart = pygal.Pie()
        chart.title = "Total Number of Self and External References"
        chart.add('Self-Reference', analyzer.get_total_in_year(True))
        chart.add('External Reference', analyzer.get_total_in_year(False))
        chart.render_to_file(base_filename + "-self-overall.svg")

        # Overall per year
        chart = pygal.StackedBar()
        chart.title = "Number of Self and External References per Year"
        chart.x_labels = map(str, analyzer.get_years())
        chart.add('Self-Reference', analyzer.get_total_in_year(True))
        chart.add('External Reference', analyzer.get_total_in_year(False))
        chart.render_to_file(base_filename + "-self-overall-year.svg")

        # External reference per year and per entry type
        _generate_per_year_per_type_chart(pygal, analyzer, base_filename + "-self-external-year.svg", False)

        # Self reference per year and per entry type
        _generate_per_year_per_type_chart(pygal, analyzer, base_filename + "-self-self-year.svg", True)


def _generate_per_year_per_type_chart(pygal, analyzer, filename, is_self):
    """

    :param pygal:
    :param analyzer:
    :param filename:
    :param is_self:
    :return:
    """
    chart = pygal.StackedBar()
    if is_self:
        title_name = "Self-References"
    else:
        title_name = "External References"
    chart.title = "Distribution of %s per Year" % title_name
    chart.x_labels = map(str, analyzer.get_years())
    chart.value_formatter = lambda x: '{:.3g}%'.format(x)
    chart.add('Article', analyzer.get_entry_type_per_year(is_self, entry.EntryType.ARTICLE))
    chart.add('In Proceedings', analyzer.get_entry_type_per_year(is_self, entry.EntryType.INPROCEEDINGS))
    chart.add('In Collection', analyzer.get_entry_type_per_year(is_self, entry.EntryType.INCOLLECTION))
    chart.add('PhD Thesis', analyzer.get_entry_type_per_year(is_self, entry.EntryType.PHDTHESIS))
    chart.add('Book', analyzer.get_entry_type_per_year(is_self, entry.EntryType.BOOK))
    chart.add('Misc', analyzer.get_entry_type_per_year(is_self, entry.EntryType.MISC))
    chart.add('Tech Report', analyzer.get_entry_type_per_year(is_self, entry.EntryType.TECHREPORT))
    chart.add('Master Thesis', analyzer.get_entry_type_per_year(is_self, entry.EntryType.MASTERTHESIS))
    chart.add('Proceedings', analyzer.get_entry_type_per_year(is_self, entry.EntryType.PROCEEDINGS))
    chart.render_to_file(filename)


class Analyzer:
    def __init__(self, initial_year):
        """

        :param initial_year:
        """
        self.initial_year = initial_year
        self.total = 0
        self.self = 0
        self.data = {
            'self': {'other': entry.create_entry_type_dict()},
            'external': {'other': entry.create_entry_type_dict()}
        }
        self.current_year = date.today().year
        for year in range(initial_year, self.current_year + 1):
            self.data['self'][year] = entry.create_entry_type_dict()
            self.data['external'][year] = entry.create_entry_type_dict()

    def process_entry(self, e):
        """

        :param e: citation entry
        """
        self.total += 1
        if e.op_self:
            self.self += 1
            type_dict = self.data['self']
        else:
            type_dict = self.data['external']

        if e.year:
            entry_year = int(e.year)
            if entry_year < self.initial_year:
                entry_year = self.initial_year

            type_dict[entry_year][e.entry_type] += 1
        else:
            type_dict['other'][e.entry_type] += 1

    def get_years(self):
        values = []
        for year in range(self.initial_year, self.current_year + 1):
            values.append(year)
        return values

    def get_total_in_year(self, is_self):
        """

        :param is_self:
        :return:
        """
        if is_self:
            type_dict = self.data['self']
        else:
            type_dict = self.data['external']

        values = []
        for year in range(self.initial_year, self.current_year + 1):
            values.append(self._get_total(type_dict, year))
        return values

    def get_entry_type_per_year(self, is_self, entry_type):
        """

        :param is_self:
        :param entry_type:
        :return:
        """
        if is_self:
            type_dict = self.data['self']
        else:
            type_dict = self.data['external']
        values = []
        for year in range(self.initial_year, self.current_year + 1):
            total = float(self._get_total(type_dict, year))
            values.append((type_dict[year][entry_type] / total) * 100)
        return values

    def _get_total(self, type_dict, year):
        """

        :param type_dict:
        :param year:
        :return:
        """
        return type_dict[year][entry.EntryType.PHDTHESIS] + \
               type_dict[year][entry.EntryType.INCOLLECTION] + \
               type_dict[year][entry.EntryType.INPROCEEDINGS] + \
               type_dict[year][entry.EntryType.ARTICLE] + \
               type_dict[year][entry.EntryType.BOOK] + \
               type_dict[year][entry.EntryType.MASTERTHESIS] + \
               type_dict[year][entry.EntryType.MISC] + \
               type_dict[year][entry.EntryType.PROCEEDINGS] + \
               type_dict[year][entry.EntryType.TECHREPORT]
