from graphviz import Graph
import rdflib
import os
from StorageHandler import StorageHandler
from rdflib.namespace import NamespaceManager
from DatasetHandler import DatasetHandler

prefixes = "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>\
            PREFIX haidt: <https://w3id.org/spice/SON/HaidtValues#>\
            PREFIX ns1: <http://www.ontologydesignpatterns.org/ont/vn/abox/role/>\
            PREFIX ns2: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#>\
            PREFIX ns3: <http://www.ontologydesignpatterns.org/ont/fred/quantifiers.owl#>\
            PREFIX owl: <http://www.w3.org/2002/07/owl#>\
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\
            PREFIX vcvf: <http://www.semanticweb.org/sdg/ontologies/2022/0/valuecore_with_value_frames.owl#>\
            PREFIX wn30instances: <https://w3id.org/framester/wn/wn30/instances/>\
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>"

query = prefixes + "SELECT ?s ?o WHERE \
    {\
    ?s vcvf:triggers ?o.\
    }"
g = rdflib.Graph()

path = os.path.join(StorageHandler.get_data_rdf_extended(), "188428164.ttl")
g.parse(path, format='ttl')

res = g.query(query)

print()
for k, v in dict(res).items():
    print(k)
    print("\t",v)
    print()

# DatasetHandler.print_dict(dict(res))

