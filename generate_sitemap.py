#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Sitemap generator for WarSampo, http://www.sotasampo.fi
"""
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


ENDPOINT = 'http://ldf.fi/warsa/sparql'

PERSON_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?uri WHERE {
  ?uri a ?class .
  ?class rdfs:subClassOf+ <http://www.cidoc-crm.org/cidoc-crm/E21_Person> .
}
"""

URL_PREFIX = 'http://www.sotasampo.fi/fi/persons/?uri='

uris = ['{prefix}{uri}'.format(prefix=URL_PREFIX, uri=quote_plus(uri)) for uri in do_query(ENDPOINT, PERSON_QUERY)]
chunks = np.array_split(uris, len(uris) // 50000 + 1)  # Split into chunks of less than 50000 URIs

# Write chunks to files
for (index, chunk) in enumerate(chunks):
    with open('sitemap_{i}.txt'.format(i=index), 'w') as file:
        file.write('\n'.join(chunk))
