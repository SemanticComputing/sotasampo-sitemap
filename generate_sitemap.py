#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Sitemap generator for WarSampo, http://www.sotasampo.fi
"""
from datetime import datetime
from urllib.parse import quote_plus
from time import sleep

import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON


def do_query(endpoint, query, retry=10):
    """
    Send a query to a SPARQL endpoint to retrieve URIs of resources.

    :param endpoint: SPARQL endpoint
    :type endpoint: str
    :param query: SPARQL query, which should return URIs with variable name ?uri
    :type query: str
    :param retry: number of retries if the query returns a malformed answer
    :type retry: int
    :return: generator of URI strings
    """
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    results = {}
    while retry:
        try:
            results = sparql.query().convert()
            retry = 0
        except ValueError:
            retry -= 1
            if retry:
                print('SPARQL query result cannot be parsed, waiting 10 seconds before retrying...')
                sleep(10)
            else:
                raise

    return (result['uri']['value'] for result in results["results"]["bindings"])


SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <sitemap>
      <loc>https://www.sotasampo.fi/sitemap_general.xml</loc>
      <lastmod>2017-08-21</lastmod>
   </sitemap>
   {sitemaps}
</sitemapindex>
"""

SITEMAP_INNER_XML = """   <sitemap>
      <loc>https://www.sotasampo.fi/{file}</loc>
      <lastmod>{lastmod}</lastmod>
   </sitemap>
"""

PAGE_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xhtml="http://www.w3.org/1999/xhtml">
  {urls}
</urlset>"""

PAGE_TEMPLATE = """ <url>
    <loc>https://www.sotasampo.fi/fi/{app}/page?uri={uri}</loc>
    <xhtml:link
                 rel="alternate"
                 hreflang="fi"
                 href="https://www.sotasampo.fi/fi/{app}/page?uri={uri}"
                 />
    <xhtml:link
                 rel="alternate"
                 hreflang="en"
                 href="https://www.sotasampo.fi/en/{app}/page?uri={uri}"
                 />
  </url>
  <url>
    <loc>https://www.sotasampo.fi/en/{app}/page?uri={uri}</loc>
    <xhtml:link
                 rel="alternate"
                 hreflang="fi"
                 href="https://www.sotasampo.fi/fi/{app}/page?uri={uri}"
                 />
    <xhtml:link
                 rel="alternate"
                 hreflang="en"
                 href="https://www.sotasampo.fi/en/{app}/page?uri={uri}"
                 />
  </url>
"""

SITEMAP_FILENAME = 'sitemap_generated_{app}_{index}.xml'

ENDPOINT = 'http://ldf.fi/warsa/sparql'

PERSON_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?uri WHERE {
  ?class rdfs:subClassOf+ <http://www.cidoc-crm.org/cidoc-crm/E21_Person> .
  ?uri a ?class .
}
"""

UNIT_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?uri WHERE {
  ?class rdfs:subClassOf+ <http://www.cidoc-crm.org/cidoc-crm/E74_Group> .
  ?uri a ?class .
}
"""

EVENT_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?uri WHERE {
  GRAPH <http://ldf.fi/warsa/events> { ?uri a [] . }
}
"""

# Get resource URIs

person_uris = [quote_plus(uri) for uri in do_query(ENDPOINT, PERSON_QUERY)]
person_chunks = np.array_split(person_uris, len(person_uris) // 25000 + 1)  # Split into chunks of less than 25000 URIs
unit_uris = [quote_plus(uri) for uri in do_query(ENDPOINT, UNIT_QUERY)]
unit_chunks = np.array_split(unit_uris, len(unit_uris) // 25000 + 1)  # Split into chunks of less than 25000 URIs
event_uris = [quote_plus(uri) for uri in do_query(ENDPOINT, EVENT_QUERY)]
event_chunks = np.array_split(event_uris, len(event_uris) // 25000 + 1)  # Split into chunks of less than 25000 URIs
sitemaps = ''

# Write chunks to files

for app, chunks in [('persons', person_chunks), ('units', unit_chunks), ('events', event_chunks)]:
    for (index, chunk) in enumerate(chunks):
        filename = SITEMAP_FILENAME.format(app=app, index=index)
        with open(filename, 'w') as file:
            file.write(PAGE_SITEMAP_XML.format(urls='\n'.join([PAGE_TEMPLATE.format(app=app, uri=page) for page in chunk])))

        sitemaps += SITEMAP_INNER_XML.format(file=filename, lastmod=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

# Write sitemap index file

sitemap_index = SITEMAP_INDEX_XML.format(sitemaps=sitemaps)
with open('sitemap_index.xml', 'w') as file:
    file.write(sitemap_index)
