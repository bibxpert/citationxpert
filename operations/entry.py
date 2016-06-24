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

import re
import sys

reload(sys);
sys.setdefaultencoding("utf8")

from tools.utils import *

log = logging.getLogger(__name__)


class EntryType:
    ARTICLE = "article"
    BOOK = "book"
    INCOLLECTION = "incollection"
    INPROCEEDINGS = "inproceedings"
    MASTERTHESIS = "mastersthesis"
    PHDTHESIS = "phdthesis"
    MISC = "misc"
    PROCEEDINGS = "proceedings"
    TECHREPORT = "techreport"


def create_entry_type_dict():
    return {
        EntryType.ARTICLE: 0,
        EntryType.BOOK: 0,
        EntryType.INCOLLECTION: 0,
        EntryType.INPROCEEDINGS: 0,
        EntryType.MASTERTHESIS: 0,
        EntryType.PHDTHESIS: 0,
        EntryType.MISC: 0,
        EntryType.PROCEEDINGS: 0,
        EntryType.TECHREPORT: 0
    }


class Entry:
    def __init__(self, entry_type=None, cite_key=None, address=None, annote=None, authors=None, booktitle=None,
                 chapter=None, crossref=None, edition=None, editor=None, howpublished=None, institution=None,
                 journal=None, key=None, month=None, note=None, number=None, organization=None, pages=None,
                 publisher=None, school=None, series=None, title=None, type=None, url=None, volume=None,
                 year=None, doi=None, main_publication=False, citations=None, op_self=None, h_index=None,
                 num_authors=None):
        """
        Create a bib entry.
        :param entry_type: type of the entry (e.g., article, inproceedings, etc.)
        :param cite_key: cite key used in latex files to reference the entry
        :param address:
        :param annote:
        :param authors: list of authors (separated by 'and')
        :param booktitle: title of the conference book
        :param chapter:
        :param crossref:
        :param edition:
        :param editors: list of editors (separated by 'and')
        :param howpublished:
        :param institution:
        :param journal: title of the journal
        :param key: publication key (usually required for 'misc' entry types)
        :param month:
        :param note:
        :param number: journal issue number
        :param organization:
        :param pages: page numbers (separated by dashes)
        :param publisher:
        :param school:
        :param series:
        :param title: publication title
        :param type:
        :param url: publication url
        :param volume: journal volume
        :param year: publication year
        :param doi: document object identifier
        :param citations: number of citations (not standard field)
        """
        self.entry_type = entry_type
        self.cite_key = cite_key
        self.address = address
        self.annote = annote
        self.authors = Authors(authors_list=authors)
        self.booktitle = _parse_booktitle(booktitle)
        self.chapter = chapter
        self.crossref = crossref
        self.edition = edition
        if editor:
            self.editors = Authors(authors_list=editor)
        else:
            self.editors = None
        self.howpublished = howpublished
        self.institution = institution
        self.journal = journal
        self.key = key
        self.month = month
        self.note = note
        self.number = number
        self.organization = organization
        self.pages = _parse_pages(pages)
        self.publisher = publisher
        self.school = school
        self.series = series
        self.title = title
        self.type = type
        self.url = url
        self.volume = volume
        self.year = year
        self.doi = doi
        # Entry internal properties
        self.main_publication = main_publication
        self.citations = citations
        self.op_self = op_self
        self.h_index = h_index
        self.num_authors = num_authors

    def __str__(self):
        entry_str = "@%s{%s,\n" % (self.entry_type, self.cite_key)
        entry_str += _print_field("author", self.authors)
        entry_str += _print_field("booktitle", self.booktitle, capitals=True)
        entry_str += _print_field("journal", self.journal, capitals=True)
        entry_str += _print_field("number", self.number)
        entry_str += _print_field("title", self.title)
        entry_str += _print_field("volume", self.volume)
        entry_str += _print_field("year", self.year)
        entry_str += _print_field("address", self.address)
        entry_str += _print_field("annote", self.annote)
        entry_str += _print_field("chapter", self.chapter)
        entry_str += _print_field("crossref", self.crossref)
        entry_str += _print_field("edition", self.edition)
        entry_str += _print_field("editor", self.editors)
        entry_str += _print_field("howpublished", self.howpublished)
        entry_str += _print_field("institution", self.institution)
        entry_str += _print_field("key", self.key)
        entry_str += _print_field("month", self.month)
        entry_str += _print_field("note", self.note)
        entry_str += _print_field("organization", self.organization)
        entry_str += _print_field("pages", self.pages)
        entry_str += _print_field("publisher", self.publisher)
        entry_str += _print_field("school", self.school)
        entry_str += _print_field("series", self.series)
        entry_str += _print_field("type", self.type)
        entry_str += _print_field("url", self.url)
        entry_str += _print_field("doi", self.doi)
        # CitationXpert properties
        entry_str += _print_field("main_publication", self.main_publication)
        entry_str += _print_field("citations", self.citations)
        entry_str += _print_field("op_self", self.op_self)
        entry_str += _print_field("h_index", self.h_index)
        entry_str += _print_field("num_authors", self.num_authors)

        entry_str += "}\n\n"
        return entry_str

    def __repr__(self):
        return self.__str__


class Authors:
    def __init__(self, authors_list=None):
        """

        :param authors_list: list of authors names
        """
        self.authors = []
        if authors_list:
            authors_list = authors_list.replace(" AND ", " and ")
            for author in authors_list.split(" and "):
                self.authors.append(Author(author.strip()))

    def has_authors(self, authors):

        for a in authors.authors:
            for author in self.authors:
                if a.first_name == author.first_name and a.last_name == author.last_name:
                    return True
        return False

    def __str__(self):
        authors = ""
        for author in self.authors:
            if len(authors) > 0:
                authors += " and "
            authors += author.__str__()
        return authors

    def __repr__(self):
        return self.__str__

    def __len__(self):
        return len(self.authors)


class Author:
    def __init__(self, author_name):
        """
        Create an author object with first and last names.
        :param author_name: name of a single author
        """
        self.first_name = ""
        self.last_name = None
        self.affiliation = None
        self.email = None
        self.country_code = None
        self.citations = 0
        self.keywords = None

        if "," in author_name:
            s = author_name.split(",")
            self.first_name = s[1].strip()
            self.last_name = s[0].strip()
        else:
            s = author_name.split(" ")
            if len(s) == 2:
                self.first_name = s[0].strip()
                self.last_name = s[1].strip()
            elif len(s) > 2:
                index = len(s) - 1
                value = s[len(s) - 2]
                if len(value) <= 2 and not value.endswith('.'):
                    self.last_name = value + " " + s[len(s) - 1]
                    index -= 1
                else:
                    self.last_name = s[len(s) - 1]
                for i in range(0, index):
                    if len(self.first_name) > 0:
                        self.first_name += " "
                    self.first_name += s[i]
            else:
                self.first_name = author_name
                self.last_name = None
                if not author_name.lower() == "others":
                    log.warning("Unable to find last name: %s" % author_name)

    def print_as_entry(self):
        entry_str = "@author{\n"
        entry_str += _print_field("first", self.first_name)
        entry_str += _print_field("last", self.last_name)
        entry_str += _print_field("affiliation", self.affiliation)
        entry_str += _print_field("email", self.email)
        entry_str += _print_field("country_code", self.country_code)
        entry_str += _print_field("citations", self.citations)
        entry_str += _print_field("keywords", self.keywords)
        entry_str += "}\n\n"
        return entry_str

    def __eq__(self, other):
        if self.last_name:
            return self.last_name == other.last_name and self.first_name == other.first_name
        else:
            return self.first_name == other.first_name

    def __str__(self):
        if self.last_name:
            return self.last_name + ", " + self.first_name
        else:
            return self.first_name

    def __repr__(self):
        return self.__str__


def _parse_pages(pages):
    """
    Parse the page number to a 2-dashes format (e.g. 100--120).
    :param pages: entry page numbers
    :return:
    """
    if pages:
        if "-" in pages:
            if not pages.count("-") == 2:
                pages = re.sub("-+", "--", pages)
        return pages
    return None


def _parse_booktitle(booktitle):
    """

    :param booktitle: entry book title
    """
    if booktitle:
        if "," in booktitle:
            bt = booktitle.split(",")
            booktitle = bt[1].strip() + " " + bt[0].strip()
        return booktitle
    return None


def _print_field(field_name, field_value, capitals=False):
    """
    Print a field in bib format if value is not none.
    :param field_name: name of the field
    :param field_value: value of the field
    :param capitals: whether to add
    :return: field in bib format or blank if field is None
    """
    if field_value is not None:
        # field_value = str(u' '.join((field_value, '')).encode('utf-8').strip())
        field_value = str(field_value).replace("_", "\_")
        field_value = str(field_value).replace("\\\\_", "\_")
        field_value = str(field_value).replace("#", "\#")
        field_value = str(field_value).replace("\\\\#", "\#")
        field_value = str(field_value).replace("$", "")
        if capitals:
            return "\t%s = {{%s}},\n" % (field_name, field_value)
        else:
            return "\t%s = {%s},\n" % (field_name, field_value)
    return ""
