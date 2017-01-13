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

SITEMAP_INDEX_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   {sitemaps}
</sitemapindex>
"""

SITEMAP_INNER_XML = """
   <sitemap>
      <loc>{location}</loc>
      <lastmod>{lastmod}</lastmod>
   </sitemap>
"""

SITEMAP_INDEX_FILE = 'sitemap_{index}.txt'

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

uris = [RESOURCE_URL.format(uri=quote_plus(uri)) for uri in do_query(ENDPOINT, PERSON_QUERY)]
chunks = np.array_split(uris, len(uris) // 50000 + 1)  # Split into chunks of less than 50000 URIs
sitemaps = ''

# Write chunks to files
for (index, chunk) in enumerate(chunks):
    filename = SITEMAP_INDEX_FILE.format(index=index)
    with open(filename, 'w') as file:
        file.write('\n'.join(chunk))

    sitemaps += SITEMAP_INNER_XML.format(location=filename, lastmod=datetime.now().isoformat())

sitemap_index = SITEMAP_INDEX_XML.format(sitemaps=sitemaps)
with open('sitemap_index.xml', 'w') as file:
    file.write(sitemap_index)
