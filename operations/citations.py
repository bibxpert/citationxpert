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
import time

from externals import scholar
from tools import loader
from tools import utils

log = logging.getLogger(__name__)


def process(titles, output=None):
    """
    Seek for the publication's citations.
    :param titles: publication titles
    :param output: output file object
    """
    log.info("Seeking for citations")

    for publication in titles:

        scholar_query = scholar.SearchScholarQuery()
        scholar_query.set_words(publication)
        scholar_query.set_num_page_results(1)

        settings = scholar.ScholarSettings()
        settings.set_citation_format(scholar.ScholarSettings.CITFORM_BIBTEX)

        querier = scholar.ScholarQuerier()
        querier.apply_settings(settings)
        querier.send_query(scholar_query)

        if len(querier.articles) == 0:
            log.warning("No entries found for the provided publication.")
            continue

        article = querier.articles[0]
        num_citations = article.attrs['num_citations'][0]
        url_citations = article.attrs['url_citations'][0]

        if num_citations == 0:
            log.warning("The publication has no citations.")
            continue

        start = 0
        # main publication
        main_bib_entry = loader.parse_bib_entry(article.citation_data, article.attrs['num_citations'][0],
                                                article.attrs['url'][0])
        main_bib_entry.main_publication = True

        utils.write_output(main_bib_entry, output)
        entries = []

        while start < num_citations:
            citations_query = CitationsScholarQuery(url_citations, start=start)
            querier = scholar.ScholarQuerier()
            querier.apply_settings(settings)
            querier.send_query(citations_query)

            for article in querier.articles:
                entries.append(loader.parse_bib_entry(article.citation_data, article.attrs['num_citations'][0],
                                                      article.attrs['url'][0]))

            start += 20
            time.sleep(1)

        # write to stdout or files
        for e in entries:
            utils.write_output(e, output)


class CitationsScholarQuery(scholar.ScholarQuery):
    """

    """

    def __init__(self, url_citations, start=0):
        scholar.ScholarQuery.__init__(self)
        self._add_attribute_type('num_results', 'Results', 0)
        self.url_citations = url_citations
        self.start = start

    def get_url(self):
        return self.url_citations + "&num=20&start=%s" % self.start
