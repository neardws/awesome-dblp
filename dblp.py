import datetime
from tqdm import tqdm
import os
import requests
from lxml import etree
from thefuzz import fuzz
import csv
from collections import namedtuple
from fake_useragent import UserAgent

DBLP_BASE_URL = 'http://dblp.uni-trier.de/'
DBLP_AUTHOR_SEARCH_URL = DBLP_BASE_URL + 'search/author'
DBLP_VENUE_SEARCH_URL = DBLP_BASE_URL + 'search/venue/api'
DBLP_PUBLICATION_SEARCH_URL = DBLP_BASE_URL + 'search/publ/api'

DBLP_PUBL_STREAM_URL = DBLP_PUBLICATION_SEARCH_URL + '?q=stream:streams/{type}/{stream_key}:&h={query_number}&f={query_first}&format=xml'

DBLP_PERSON_URL = DBLP_BASE_URL + 'pers/xk/{urlpt}'
DBLP_PUBLICATION_URL = DBLP_BASE_URL + 'rec/bibtex/{key}.xml'

user_agent = UserAgent()

class LazyAPIData(object):
    def __init__(self, lazy_attrs):
        self.lazy_attrs = set(lazy_attrs)
        self.data = None

    def __getattr__(self, key):
        if key in self.lazy_attrs:
            if self.data is None:
                self.load_data()
            return self.data[key]
        raise AttributeError(key)

    def load_data(self):
        pass

class Author(LazyAPIData):
    """
    Represents a DBLP author. All data but the author's key is lazily loaded.
    Fields that aren't provided by the underlying XML are None.
    Attributes:
    name - the author's primary name record
    publications - a list of lazy-loaded Publications results by this author
    homepages - a list of author homepage URLs
    homonyms - a list of author aliases
    """
    def __init__(self, urlpt):
        self.urlpt = urlpt
        self.xml = None
        super(Author, self).__init__(['name','publications','homepages',
                                        'homonyms'])

    def load_data(self):
        headers = {'User-Agent': user_agent.random}
        resp = requests.get(DBLP_PERSON_URL.format(urlpt=self.urlpt),
                            headers=headers)
        xml = resp.content
        self.xml = xml
        root = etree.fromstring(xml)
        data = {
            'name':root.attrib['name'],
            'publications':[Publication(key=key) for key in 
                            root.xpath('/dblpperson/dblpkey[not(@type)]/text()')],
            'homepages':root.xpath(
                '/dblpperson/dblpkey[@type="person record"]/text()'),
            'homonyms':root.xpath('/dblpperson/homonym/text()')
        }
        self.data = data

class Venue(LazyAPIData):
    """
    Represents a DBLP venue. All data but the venue's key is lazily loaded.
    Fields that aren't provided by the underlying XML are None.
    Attributes:
    name - the venue's primary name record
    publications - a list of lazy-loaded Publications results by this venue
    acronym - the acronym of the venue
    type - the type of the venue
    url - the URL of the venue
    """
    def __init__(self, hit, query_number, query_first):
        self.xml = None
        self.name = hit.xpath('info/venue/text()')[0]
        self.type = hit.xpath('info/type/text()')[0]
        self.url = hit.xpath('info/url/text()')[0]
        try:
            self.acronym = hit.xpath('info/acronym/text()')[0]
        except IndexError:
            self.acronym = self.url.split('/')[-1]
        self.query_number = query_number
        self.query_first = query_first
        self.steam_key = self.acronym
        super(Venue, self).__init__(['publications'])

    def load_data(self):
        if self.type == 'Journal':
            type = 'journals'
        elif self.type == 'Conference':
            type = 'conf'
        elif self.type == 'Conference or Workshop':
            type = 'conf'
        else:
            raise ValueError('Unknown venue type: {}'.format(self.type))
        headers = {'User-Agent': user_agent.random}
        resp = requests.get(DBLP_PUBL_STREAM_URL.format(
            type=type,
            stream_key=self.steam_key.lower(),
            query_number=self.query_number,
            query_first=self.query_first),
            headers=headers)
        xml = resp.content
        self.xml = xml
        root = etree.fromstring(xml)
        data = {
            'publications':[Publication(key=key.text) for key in 
                            root.iter('key')]
        }
        self.data = data

def first_or_none(seq):
    try:
        return next(iter(seq))
    except StopIteration:
        pass

Publisher = namedtuple('Publisher', ['name', 'href'])
Series = namedtuple('Series', ['text','href'])
Citation = namedtuple('Citation', ['reference','label'])

class Publication(LazyAPIData):
    """
    Represents a DBLP publication- eg, article, inproceedings, etc. All data but
    the key is lazily loaded. Fields that aren't provided by the underlying XML
    are None.
    Attributes:
    type - the publication type, eg "article", "inproceedings", "proceedings",
    "incollection", "book", "phdthesis", "mastersthessis"
    sub_type - further type information, if provided- eg, "encyclopedia entry",
    "informal publication", "survey"
    title - the title of the work
    authors - a list of author names
    journal - the journal the work was published in, if applicable
    volume - the volume, if applicable
    number - the number, if applicable
    chapter - the chapter, if this work is part of a book or otherwise
    applicable
    pages - the page numbers of the work, if applicable
    isbn - the ISBN for works that have them
    ee - an ee URL
    crossref - a crossrel relative URL
    publisher - the publisher, returned as a (name, href) named tuple
    citations - a list of (text, label) named tuples representing cited works
    series - a (text, href) named tuple describing the containing series, if
    applicable
    """
    def __init__(self, key=None):
        self.key = key
        self.xml = None
        super(Publication, self).__init__( ['type', 'sub_type', 'mdate',
                'authors', 'editors', 'title', 'year', 'month', 'journal',
                'volume', 'number', 'chapter', 'pages', 'ee', 'isbn', 'url',
                'booktitle', 'crossref', 'publisher', 'school', 'citations',
                'series'])

    def load_data(self):
        headers = {'User-Agent': user_agent.random}
        resp = requests.get(DBLP_PUBLICATION_URL.format(key=self.key), 
                            headers=headers)
        xml = resp.content
        self.xml = xml
        root = etree.fromstring(xml)
        publication = first_or_none(root.xpath('/dblp/*[1]'))
        if publication is None:
            raise ValueError
        data = {
            'type':publication.tag,
            'sub_type':publication.attrib.get('publtype', None),
            'mdate':publication.attrib.get('mdate', None),
            'authors':publication.xpath('author/text()'),
            'editors':publication.xpath('editor/text()'),
            'title':publication.xpath('title/text()')[0],
            'year':int(first_or_none(publication.xpath('year/text()'))),
            'month':first_or_none(publication.xpath('month/text()')),
            'journal':first_or_none(publication.xpath('journal/text()')),
            'volume':first_or_none(publication.xpath('volume/text()')),
            'number':first_or_none(publication.xpath('number/text()')),
            'chapter':first_or_none(publication.xpath('chapter/text()')),
            'pages':first_or_none(publication.xpath('pages/text()')),
            'ee':first_or_none(publication.xpath('ee/text()')),
            'isbn':first_or_none(publication.xpath('isbn/text()')),
            'url':first_or_none(publication.xpath('url/text()')),
            'booktitle':first_or_none(publication.xpath('booktitle/text()')),
            'crossref':first_or_none(publication.xpath('crossref/text()')),
            'publisher':first_or_none(publication.xpath('publisher/text()')),
            'school':first_or_none(publication.xpath('school/text()')),
            'citations':[Citation(c.text, c.attrib.get('label',None))
                        for c in publication.xpath('cite') if c.text != '...'],
            'series':first_or_none(Series(s.text, s.attrib.get('href', None))
                    for s in publication.xpath('series'))
        }
        self.data = data

def search(type, query_str, query_number=None, query_first=None):
    headers = {'User-Agent': user_agent.random}
    if type == 'author':
        resp = requests.get(DBLP_AUTHOR_SEARCH_URL, params={'xauthor':query_str}, headers=headers)
        root = etree.fromstring(resp.content)
        return [Author(urlpt) for urlpt in root.xpath('/authors/author/@urlpt')]
    elif type == 'venue':
        resp = requests.get(DBLP_VENUE_SEARCH_URL, params={'q':query_str, 'format':'xml'}, headers=headers)
        root = etree.fromstring(resp.content)
        return [Venue(hit, query_number, query_first) for hit in root.iter('hit')]
    elif type == 'publication':
        resp = requests.get(DBLP_PUBLICATION_SEARCH_URL, params={'q':query_str, 'format':'xml'}, headers=headers)
        root = etree.fromstring(resp.content)
        return [Publication(key=hit.text) for hit in root.iter('key')]

def search_by_keywords(keywords: list, query_number: int, maximum_query_number: int):
    dayTime = datetime.datetime.now().strftime('%Y-%m-%d')
    hourTime = datetime.datetime.now().strftime('%H-%M-%S')
    csv_name = dayTime + '_' + hourTime + '_' + keywords[0] + '.csv'
    range_number = int(query_number / maximum_query_number)
    for keyword in keywords:
        for i in tqdm(range(range_number)):
            publications = []
            headers = {'User-Agent': user_agent.random}
            resp = requests.get(DBLP_PUBLICATION_SEARCH_URL, params={'q':keyword, 'h':maximum_query_number, 'f':i*maximum_query_number, 'format':'xml'}, headers=headers)
            root = etree.fromstring(resp.content)
            for hit in root.iter('hit'):
                hit_type = hit.xpath('info/type/text()')[0]
                if hit_type == 'Journal Articles':
                    venue_str = hit.xpath('info/venue/text()')[0]
                    if venue_str.startswith('ACM Trans.') or \
                        venue_str.startswith('IEEE Trans.'):
                        publication = Publication(key=hit.xpath('info/key/text()')[0])
                        publication.load_data()
                        publications.append(publication)
                elif hit_type == 'Conference and Workshop Papers':
                    conf_str = hit.xpath('info/key/text()')[0].split('/')[1]
                    if conf_str == 'infocom' or conf_str == 'sigcomm' or \
                        conf_str == 'mobicom' or conf_str == 'nsdi':
                        publication = Publication(key=hit.xpath('info/key/text()')[0])
                        publication.load_data()
                        publications.append(publication)
            save_publications_to_csv(publications, csv_name)

def search_by_keywords_venues(keywords: list, venue_names: list, query_number: int, maximum_query_number: int):
    dayTime = datetime.datetime.now().strftime('%Y-%m-%d')
    hourTime = datetime.datetime.now().strftime('%H-%M-%S')
    csv_name = dayTime + '_' + hourTime + '_' +keywords[0] + '_' + venue_names[0].replace(' ', '_') + '.csv'
    range_number = int(query_number / maximum_query_number)
    print('Searching for venues...')
    for venue_name in tqdm(venue_names):
        for i in range(range_number):
            venue = search('venue', venue_name, query_number=maximum_query_number, query_first=i*maximum_query_number)[0]
            publications = []
            for publication in tqdm(venue.publications):
                for keyword in keywords:
                    score = fuzz.partial_ratio(keyword, publication.title)
                    if score > 60:
                        publications.append(publication)
                        break;
            save_publications_to_csv(publications, csv_name)
    print('Done!')

def save_publications_to_csv(publications, csv_name):
    is_file_exist = os.path.isfile(csv_name)
    with open(csv_name, 'a+', newline='') as csvfile:
        fieldnames = ['type', 'sub_type', 'mdate', 'authors', 'editors',
                            'title', 'year', 'month', 'journal', 'volume', 'number', 
                            'chapter', 'pages', 'ee', 'isbn', 'url', 'booktitle',
                            'crossref', 'publisher', 'school', 'citations', 'series']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not is_file_exist:
            writer.writeheader()
        for publication in publications:
            if not publication.data:
                publication.load_data()
            writer.writerow(publication.data)