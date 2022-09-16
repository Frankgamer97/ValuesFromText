#!/usr/bin/env python
# coding: utf-8

# In[9]:


def scrittura_file(df, path, nome_file, header):
    if not os.path.isfile(nome_file):
        df.to_csv(nome_file, index=False, header=header)
    else:
        df.to_csv(nome_file, mode='a', index=False, header=False)


# In[2]:


get_ipython().system('pip install rdflib')
get_ipython().system('pip install SPARQLWrapper')


# In[22]:



import requests
import rdflib
from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode
import SPARQLWrapper
from SPARQLWrapper import SPARQLWrapper, JSON, N3, TURTLE, RDF, CSV
import json
import os
from collections import defaultdict
import pandas as pd
import openpyxl
from openpyxl import Workbook
from openpyxl import load_workbook



headers = {
    'accept': 'text/turtle',
    'Authorization': 'Bearer a7727b8c-aa1e-39d4-8b34-3977ec1c73f5',
}

# here you declare the endpoint, you can have it in localhost or you can use the online Framester one

valuesparql = SPARQLWrapper('http://localhost:3030/ValueNet/query') # change with: 'http://etna.istc.cnr.it/framester2/sparql'



comment = URIRef("http://www.w3.org/2000/01/rdf-schema#comment")
sample_phrase = URIRef("http://sample_phrase.org/")



all_names = [Namespace("https://w3id.org/framester/wn/wn30/"), Namespace("https://w3id.org/framester/vn/vn31/data/"), Namespace("<http://dbpedia.org/resource/"), Namespace("https://w3id.org/framester/data/framestercore/"), Namespace("https://w3id.org/framester/pb/pbdata/"), Namespace("https://w3id.org/framester/framenet/abox/gfe/"), Namespace("https://w3id.org/framester/pb/pbschema/"), Namespace("https://w3id.org/framester/wn/wn30/wordnet-verbnountropes/"), Namespace("https://w3id.org/framester/data/framesterrole/"), Namespace("http://babelnet.org/rdf/"), Namespace("https://w3id.org/framester/framenet/abox/fe/"), Namespace("https://w3id.org/framester/framenet/abox/frame/"), Namespace("https://w3id.org/framester/data/framestersyn/") ]



# this function makes a call to FRED to generate a graph from sentence (you can save it as Turtle file .ttl)

def test_graph(txt):
  params = (
      ('text', txt), #cv),
      ('wfd_profile', 'b'),
      ('textannotation', 'earmark'),
      ('wfd', True),
      ('roles', False),
      ('alignToFramester', True),
      ('semantic-subgraph', True)
  )
  response = requests.get('http://wit.istc.cnr.it/stlab-tools/fred', headers=headers, params=params)
  #return response.text 
  with open('out1.ttl','w') as out1: 
    out1.write(response.text)


# this function find value triggers

def find_trigs(input,txt):    
    
# generate graphs to be used later 

  g_valueObj = rdflib.Graph()
  g_valueSubj = rdflib.Graph()

  g = rdflib.Graph()
  finalg = rdflib.Graph()
  cell_graph = g.parse(input, format="ttl")

  # create list of subject and objects of triples to store entities URIs in order to iterate on them

  sub = []
  obj = []
  for s,p,o in cell_graph:
        
        # URIs generated in FRED graph could be different from those in Framester, therefore the replacement

        s = str(s).replace("http://www.w3.org/2006/03/wn/wn30/instances", "https://w3id.org/framester/wn/wn30/instances")
        o = str(o).replace("http://www.w3.org/2006/03/wn/wn30/instances", "https://w3id.org/framester/wn/wn30/instances")
        s = str(s).replace("http://www.ontologydesignpatterns.org/ont/vn/data", "https://w3id.org/framester/vn/vn31/data")
        o = str(o).replace("http://www.ontologydesignpatterns.org/ont/vn/data", "https://w3id.org/framester/vn/vn31/data")
        
        for k in all_names:
            if k in s:
                vs_list = []
                vs_list.append(s)
                
                for z in vs_list:
                    
                    # query to retrieve all subjects of triples which trigger some value in ValueNet
                    
                    queryValueSubj = (
                    '''
                    PREFIX vcvf: <http://www.semanticweb.org/sdg/ontologies/2022/0/valuecore_with_value_frames.owl#>
                    PREFIX haidt: <https://w3id.org/spice/SON/HaidtValues#>

                    CONSTRUCT { <'''+z+'''> vcvf:triggers ?o . }
                    WHERE
                      { <'''+z+'''> vcvf:triggers ?o . }
                    '''
                    )
                    
                    # store the triple in a graph
                    
                    valuesparql.setQuery(queryValueSubj)
                    valuesparql.setReturnFormat(TURTLE)
                    resultsValueSubj = valuesparql.query().convert()
                    g_valueSubj = g_valueSubj.parse(resultsValueSubj, format="ttl")
                    
                    

            if k in o:
                vo_list = []
                vo_list.append(o)
                for q in vo_list:
                    
                    # query to retrieve all objects of triples which trigger some value in ValueNet

                    
                    queryValueObj = (
                    '''
                    PREFIX vcvf: <http://www.semanticweb.org/sdg/ontologies/2022/0/valuecore_with_value_frames.owl#>
                    PREFIX haidt: <https://w3id.org/spice/SON/HaidtValues#>

                    CONSTRUCT { <'''+o+'''> vcvf:triggers ?o . }
                    WHERE
                    { <'''+o+'''> vcvf:triggers ?o . }
                    '''
                    )

                    # store the triple in a graph
                    
                    valuesparql.setQuery(queryValueObj)
                    valuesparql.setReturnFormat(TURTLE)
                    resultsValueObj = valuesparql.query().convert()
                    g_valueObj = g_valueObj.parse(resultsValueObj, format="ttl")
                    
                    
               
                    
        # merge all graphs in a new graph

        finalg = cell_graph + g_valueSubj + g_valueObj
        


        sub += [s for s,p,o in finalg if 'triggers' in p]
        obj += [o for s,p,o in finalg if 'triggers' in p]
        
  for s,p,o in g_valueObj:
    print(s,p,o)

     

  diz = {'sub':sub,
         'obj':obj}  
  return diz


# In[4]:


get_ipython().system('pip install sklearn')


# In[23]:


from urllib.error import HTTPError

import pandas as pd
import time

t = 20

# here you declare the path to your file to be tested

doc = pd.read_csv('/Users/sdg/Downloads/value_detector_test1.csv')

for index,row in doc.iterrows():
  txt = row['txt']
  label = row['label']
  try:
    out1 = test_graph(txt)
    out2 = find_trigs('out1.ttl',txt)

    # this is just to have a cleaner output without the full URI but only with the value name
    
    predizione = [ele.replace('https://w3id.org/spice/SON/HaidtValues#','').strip().lower() for ele in list(set([str(ele) for ele in out2['obj']]))]

    print(predizione)

    # in "label" you can put e.g. "loyalty-betrayal" from social chemistry file
    
    out = {'sent':[txt],
        'label':[label],
        'pred':[', '.join(predizione)],
        'trig':[', '.join(list(set([str(ele) for ele in out2['sub']])))]}
    print(out)

    df = pd.DataFrame(out)
    scrittura_file (df, '', 'value_detector_test1.csv', [k for k in out.keys()])
    #if index==1:break

    print(f"{index}/{len(doc)}")

    if (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout):
      time.sleep(t)

  except Exception:
    continue


# In[53]:


#metriche 
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn import metrics, model_selection, preprocessing
from sklearn.metrics import classification_report


# this is eventually to test some metrics, to be fine tuned according to your needs

doc = pd.read_csv('value_detector_test1.csv')

mapping = {
  0: 'care',
  1: 'purity',
  2: 'non-moral',
  3: 'loyalty',
  4: 'cheating',
  5: 'fairness',
  6: 'subversion',  
  7: 'betrayal',
  8: 'degradation',
  9: 'harm',
  10: 'authority'}

label =  [[k for c in ele.split(',') for k,v in mapping.items() if c.strip() == v] for ele in doc['label']]
predizioni = [[k for c in str(ele).split(',') for k,v in mapping.items() if c.strip() == v] for ele in doc['pred']]

def one_hot (etichette):
  out = []
  for ele in etichette:
    out_ = [0]*len(mapping)
    for num in ele:
      out_[num]=1
    out+=[out_]
  return out

label = one_hot(label)
predizioni = one_hot(predizioni)



print(metrics.classification_report(label, predizioni, digits=2 , target_names = [v for v in mapping.values()]))


# In[ ]:




