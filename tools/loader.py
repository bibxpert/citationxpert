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
import re

from operations import entry
from tools import utils

log = logging.getLogger(__name__)


def load_entries(filename):
    """

    :param filename:
    :return:
    """
    log.debug("Parsing file: %s" % filename)

    entries = []

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line.startswith("@"):
                buffer_line = ""

            buffer_line += line + "\n"

            if line.startswith("}"):
                entries.append(parse_bib_entry(buffer_line))

    return entries


def load_list_of_entries(list_of_files):
    """
    Load entries from list of files. The method also seeks for duplicated entries and remove them.
    :param list_of_files: list of citation files
    :return: list of entries from all citation files
    """
    publication_entries = []
    entries = []
    titles = []

    for filename in list_of_files:
        entries_list = load_entries(filename)

        for e in entries_list:
            if e.main_publication:
                publication_entries.append(e)
            elif e.title not in titles:
                titles.append(e.title)
                entries.append(e)

    return publication_entries, entries


def parse_bib_entry(data, num_citations=None, url=None):
    """

    :param data:
    :param num_citations:
    :param url:
    :return:
    """
    lines = data.split('\n')
    if not num_citations:
        num_citations = 0
    new_entry = {
        'citations': num_citations,
        'url': url
    }
    values = {}

    for line in lines:
        line = line.strip()

        if line.startswith("%") or len(line) == 0:
            continue

        if line.startswith("@"):
            # bib type and key
            index = re.search("{|\(", line).start()
            bib_type = _parse_bib_type(line[1:index].strip())
            key = line[index + 1:line.index(',')].strip()
            new_entry['bib_type'] = bib_type
            new_entry['cite_key'] = key

        else:
            # other fields
            if line.startswith("}"):
                for key in values:
                    if values[key]:
                        new_entry[key] = values[key]
                    else:
                        log.debug("[%s] Ignoring entry '%s': value is empty." % (new_entry['cite_key'], key))
                return _add_entry(new_entry)

            else:
                s = re.split("=\s*\"|=\s*\{|=\s*", line)
                key = s[0].strip().lower()
                if len(key) == 0:
                    continue
                value = s[1].strip()
                if key == "howpublished":
                    value = value.replace("\\url{", "")
                    value = value.replace("}}", "")

                if value.startswith("{") or value.startswith("\""):
                    value = value[1:len(value)]
                if value.endswith("}") or value.endswith("\"") or value.endswith(","):
                    value = value[0:len(value) - 1]
                if value.endswith("},") or value.endswith("\","):
                    value = value[0:len(value) - 2]
                value = re.sub("{|\"|}", "", value)
                values[key] = value


def load_authors(list_of_files):
    """

    :param list_of_files: list of authors files
    :return: list of authors
    """
    authors = []
    author = {}

    for authors_file in list_of_files:
        with open(authors_file) as f:
            for line in f:
                line = line.strip()

                if line.startswith("@author"):
                    author = {}

                elif line.startswith("}"):
                    author_obj = _create_author(author)
                    if author_obj not in authors:
                        authors.append(author_obj)

                elif len(line) > 0:
                    s = re.split("=\s*\"|=\s*\{|=\s*", line)
                    key = s[0].strip().lower()
                    value = s[1].strip()
                    if value.startswith("{") or value.startswith("\""):
                        value = value[1:len(value)]
                    if value.endswith("}") or value.endswith("\"") or value.endswith(","):
                        value = value[0:len(value) - 1]
                    if value.endswith("},") or value.endswith("\","):
                        value = value[0:len(value) - 2]
                    value = re.sub("{|\"|}", "", value)
                    author[key] = value

    return authors


def _create_author(author_dict):
    """

    :param author_dict:
    :return: an author object
    """
    if 'last' in author_dict and author_dict['last']:
        author = entry.Author(author_dict['last'] + ', ' + author_dict['first'])
    else:
        author = entry.Author(author_dict['first'])

    if 'affiliation' in author_dict and author_dict['affiliation']:
        author.affiliation = author_dict['affiliation']
    if 'email' in author_dict and author_dict['email']:
        author.email = author_dict['email']
    if 'country_code' in author_dict and author_dict['country_code']:
        author.country_code = author_dict['country_code']
    if 'citations' in author_dict and author_dict['citations']:
        author.citations = author_dict['citations']

    return author


def _parse_bib_type(bib_type_name):
    """

    :param bib_type_name:
    :return:
    """
    if not bib_type_name:
        log.error("Bib type not found.")
        exit(1)

    if bib_type_name.lower() == entry.EntryType.ARTICLE:
        return entry.EntryType.ARTICLE
    if bib_type_name.lower() == entry.EntryType.BOOK:
        return entry.EntryType.BOOK
    if bib_type_name.lower() == entry.EntryType.INCOLLECTION:
        return entry.EntryType.INCOLLECTION
    if bib_type_name.lower() == entry.EntryType.INPROCEEDINGS:
        return entry.EntryType.INPROCEEDINGS
    if bib_type_name.lower() == entry.EntryType.MASTERTHESIS:
        return entry.EntryType.MASTERTHESIS
    if bib_type_name.lower() == entry.EntryType.MISC:
        return entry.EntryType.MISC
    if bib_type_name.lower() == entry.EntryType.PHDTHESIS:
        return entry.EntryType.PHDTHESIS
    if bib_type_name.lower() == entry.EntryType.PROCEEDINGS:
        return entry.EntryType.PROCEEDINGS
    if bib_type_name.lower() == entry.EntryType.TECHREPORT:
        return entry.EntryType.TECHREPORT

    log.error("Unable to parse type: %s" % bib_type_name)
    exit(1)


def _add_entry(new_entry):
    log.info("Adding entry: %s" % new_entry["cite_key"])
    return entry.Entry(
        entry_type=new_entry["bib_type"],
        cite_key=new_entry["cite_key"],
        address=_get_value("address", new_entry),
        annote=_get_value("annote", new_entry),
        authors=_get_value("author", new_entry),
        booktitle=_get_value("booktitle", new_entry),
        chapter=_get_value("chapter", new_entry),
        crossref=_get_value("crossref", new_entry),
        doi=_get_value("doi", new_entry),
        edition=_get_value("edition", new_entry),
        editor=_get_value("editor", new_entry),
        howpublished=_get_value("howpublished", new_entry),
        institution=_get_value("institution", new_entry),
        journal=_get_value("journal", new_entry),
        key=_get_value("key", new_entry),
        month=_get_value("month", new_entry),
        note=_get_value("note", new_entry),
        number=_get_value("number", new_entry),
        organization=_get_value("organization", new_entry),
        pages=_get_value("pages", new_entry),
        publisher=_get_value("published", new_entry),
        school=_get_value("school", new_entry),
        series=_get_value("series", new_entry),
        title=_get_value("title", new_entry),
        type=_get_value("type", new_entry),
        url=_get_value("url", new_entry),
        volume=_get_value("volume", new_entry),
        year=_get_value("year", new_entry),
        main_publication=_get_value("main_publication", new_entry),
        citations=_get_value("citations", new_entry),
        op_self=_get_value("op_self", new_entry),
        h_index=_get_value("h_index", new_entry),
    )


def _get_value(key, entry):
    """

    :param key:
    :param entry:
    :return:
    """
    if key in entry:
        if entry[key] and str(entry[key]).lower() == "true":
            return True
        elif entry[key] and str(entry[key]).lower() == "false":
            return False
        return entry[key]
    return None
