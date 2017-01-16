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
      <loc>http://www.sotasampo.fi/sitemap_general.txt</loc>
      <lastmod>2017-01-16</lastmod>
   </sitemap>
   {sitemaps}
</sitemapindex>
"""

SITEMAP_INNER_XML = """   <sitemap>
      <loc>http://www.sotasampo.fi/{file}</loc>
      <lastmod>{lastmod}</lastmod>
   </sitemap>
"""

SITEMAP_FILENAME = 'sitemap_generated_{index}.txt'

ENDPOINT = 'http://ldf.fi/warsa/sparql'

PERSON_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?uri WHERE {
  ?uri a ?class .
  ?class rdfs:subClassOf+ <http://www.cidoc-crm.org/cidoc-crm/E21_Person> .
}
"""

RESOURCE_URL = 'http://www.sotasampo.fi/fi/persons/?uri={uri}'

# Get resource URIs

uris = [RESOURCE_URL.format(uri=quote_plus(uri)) for uri in do_query(ENDPOINT, PERSON_QUERY)]
chunks = np.array_split(uris, len(uris) // 50000 + 1)  # Split into chunks of less than 50000 URIs
sitemaps = ''

# Write chunks to files

for (index, chunk) in enumerate(chunks):
    filename = SITEMAP_FILENAME.format(index=index)
    with open(filename, 'w') as file:
        file.write('\n'.join(chunk))

    sitemaps += SITEMAP_INNER_XML.format(file=filename, lastmod=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

# Write sitemap index file

sitemap_index = SITEMAP_INDEX_XML.format(sitemaps=sitemaps)
with open('sitemap_index.xml', 'w') as file:
    file.write(sitemap_index)
