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
import time
import urllib

from datetime import date
from externals import scholar
from operations import entry
from tools import loader
from tools import utils

log = logging.getLogger(__name__)

# Import BeautifulSoup -- try 4 first, fall back to older
try:
    from bs4 import BeautifulSoup
except ImportError:
    try:
        from BeautifulSoup import BeautifulSoup
    except ImportError:
        log.error('We need BeautifulSoup, sorry...')
        exit(1)


def process(citations_file, output=None, plot=False):
    """

    :param citations_file: list of citations files
    :param output: output file object
    :param plot: whether charts should be plotted
    """
    log.info("Computing citations per author")
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
    pe_authors_list = []

    for pe in publication_entries:
        if int(pe.year) < minor_year:
            minor_year = int(pe.year)
        # publication authors list
        for author in pe.authors.authors:
            if author not in pe_authors_list and not author.first_name == 'others':
                pe_authors_list.append(author)

    # create data analysis structure
    analyzer = Analyzer(minor_year, pe_authors_list)

    for e in entries:
        analyzer.process(e)

    for pe in publication_entries:
        pe.num_authors = analyzer.get_num_authors()
        utils.write_output(pe, output)

    for e in entries:
        utils.write_output(e, output)

    base_filename = os.path.splitext(citations_file[0])[0]
    authors_file = open(base_filename + '.authors', 'w')

    gs_authors = []
    authors_bulk = []
    num_queried_authors = 0

    for author in analyzer.all_authors:
        if len(authors_bulk) < 10 and num_queried_authors < len(analyzer.all_authors):
            authors_bulk.append(author)
            num_queried_authors += 1

        else:
            # Query for authors metadata
            log.info("Querying for %s authors metadata." % len(authors_bulk))
            author_query = AuthorScholarQuery(authors_bulk)
            querier = AuthorScholarQuerier()
            querier.send_query(author_query)

            for a in querier.authors:
                # check if author corresponds to request
                author_to_remove = None
                for ab in authors_bulk:
                    if ab.first_name.split(' ')[0].lower() in a.first_name.lower():
                        if not ab.last_name or not a.last_name or \
                                        ab.last_name.split(' ')[-1].lower() in a.last_name.lower():
                            author_to_remove = ab
                            break
                if not author_to_remove:
                    continue

                authors_bulk.remove(author_to_remove)

                # avoid duplicated google scholar entries
                if a in gs_authors:
                    log.info("Skipping duplicated author: %s" % author)
                    continue
                utils.write_output(a.print_as_entry(), authors_file)
                gs_authors.append(a)

            authors_bulk = []
            time.sleep(1)

    if plot:
        # plot solid gauge with number of authors having google scholar profile
        if not utils.check_module('pygal'):
            log.error("Unable to generate plot, cannot find module 'pygal'.")
            exit(1)
        pygal = __import__('pygal')

        base_filename = os.path.splitext(citations_file[0])[0]

        config = pygal.Config()
        config.show_legend = False
        chart = pygal.SolidGauge(config=config,
                                 half_pie=True, inner_radius=0.70,
                                 style=pygal.style.styles['default'](value_font_size=10))
        chart.add('', [{'value': len(gs_authors), 'max_value': len(analyzer.all_authors)}])
        chart.render_to_file(base_filename + "-author-num.svg")


class Analyzer:
    def __init__(self, initial_year, pe_authors_list):
        """

        :param initial_year:
        """
        self.initial_year = initial_year
        self.current_year = date.today().year
        self.pe_authors_list = pe_authors_list
        self.all_authors = []
        self.yearly_authors = {}
        for i in range(initial_year, self.current_year + 1):
            self.yearly_authors[i] = []

    def process(self, e):
        """

        :param e: citation entry
        """
        for author in e.authors.authors:
            if author not in self.all_authors and author not in self.pe_authors_list:
                self.all_authors.append(author)
            if e.year:
                citation_year = int(e.year)
                if citation_year < self.initial_year:
                    citation_year = self.initial_year

                if author not in self.yearly_authors[citation_year]:
                    self.yearly_authors[citation_year].append(author)

    def get_num_authors(self):
        return len(self.all_authors)


class AuthorScholarQuery(scholar.ScholarQuery):
    """

    """

    def __init__(self, authors_list):
        scholar.ScholarQuery.__init__(self)
        self._add_attribute_type('num_results', 'Results', 0)

        self.authors_list = authors_list
        self.url = 'https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors='

    def get_url(self):
        authors_url = ""
        for author in self.authors_list:
            if len(authors_url) > 0:
                authors_url += urllib.quote("|")

            a_url = ""
            if author.last_name:
                a_url += author.first_name + ' ' + author.last_name
            else:
                a_url += author.first_name
            a_url.replace(' ', '+')

            authors_url += urllib.quote('"' + a_url + '"')

        return self.url + authors_url


class AuthorScholarQuerier(scholar.ScholarQuerier):
    """

    """

    def __init__(self):
        scholar.ScholarQuerier.__init__(self)
        self.authors = []

    def send_query(self, query):
        self.query = query

        html = self._get_http_response(url=query.get_url(),
                                       log_msg='dump of query response HTML',
                                       err_msg='results retrieval failed')

        if html is None:
            return

        self.parse(html)

    class Parser(scholar.ScholarQuerier.Parser):

        def parse(self, html):
            self.soup = BeautifulSoup(html)
            self._parse_globals()
            authors_list = self.soup.findAll(AuthorScholarQuerier._tag_results_checker)
            if len(authors_list) == 0:
                return

            authors = []
            for a in authors_list:
                author = None
                for tag in a:
                    if not hasattr(tag, 'name'):
                        continue

                    if tag.name == 'div' and self._tag_has_class(tag, 'gsc_1usr_text'):
                        if tag.h3 and tag.h3.a:
                            author = entry.Author(''.join(tag.h3.a.findAll(text=True)))

                        for tag2 in tag.findAll('div'):
                            if tag2.name == 'div' and self._tag_has_class(tag2, 'gsc_1usr_aff'):
                                author.affiliation = ''.join(tag2.findAll(text=True))

                            elif tag2.name == 'div' and self._tag_has_class(tag2, 'gsc_1usr_emlb'):
                                author.email = ''.join(tag2.findAll(text=True))
                                author.country_code = utils.parse_country_code(author.email.split('.')[-1])

                            elif tag2.name == 'div' and self._tag_has_class(tag2, 'gsc_1usr_cby'):
                                author.citations = (''.join(tag2.findAll(text=True))).split(' ')[-1]

                            elif tag2.name == 'div' and self._tag_has_class(tag2, 'gsc_1usr_int'):
                                keywords = ''
                                for tag3 in tag2.findAll('a'):
                                    if tag3.name == 'a' and self._tag_has_class(tag3, 'gsc_co_int'):
                                        if len(keywords) > 0:
                                            keywords += ', '
                                        keywords += ''.join(tag3.findAll(text=True))
                                author.keywords = keywords
                if author:
                    authors.append(author)

            if len(authors) > 0:
                self.handle_article(authors)

        def handle_article(self, art):
            self.querier.authors = art

    @staticmethod
    def _tag_results_checker(tag):
        return tag.name == 'div' \
               and scholar.ScholarArticleParser._tag_has_class(tag, 'gsc_1usr')
