from lib2to3.pgen2 import token
from re import sub
from StorageHandler import StorageHandler

from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag, download
from nltk.corpus import wordnet

import pandas as pd
import gdown
import zipfile
import os
import requests
import rdflib

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

all_names = [
    Namespace("https://w3id.org/framester/wn/wn30/"), 
    Namespace("https://w3id.org/framester/vn/vn31/data/"), 
    Namespace("<http://dbpedia.org/resource/"), 
    Namespace("https://w3id.org/framester/data/framestercore/"), 
    Namespace("https://w3id.org/framester/pb/pbdata/"), 
    Namespace("https://w3id.org/framester/framenet/abox/gfe/"), 
    Namespace("https://w3id.org/framester/pb/pbschema/"), 
    Namespace("https://w3id.org/framester/wn/wn30/wordnet-verbnountropes/"), 
    Namespace("https://w3id.org/framester/data/framesterrole/"), 
    Namespace("http://babelnet.org/rdf/"), 
    Namespace("https://w3id.org/framester/framenet/abox/fe/"), 
    Namespace("https://w3id.org/framester/framenet/abox/frame/"), 
    Namespace("https://w3id.org/framester/data/framestersyn/") 
]

valuesparql = SPARQLWrapper('http://localhost:3030/ValueNet/sparql')

class DatasetHandler:

    datasetFileName = "social-chem"
    drive_id = "1aUd_epnAqGzLkRBw4D1fsBdcWgIE-PvO"

    @staticmethod
    def __get_dataset_zip_path():
        return os.path.join(StorageHandler.get_tmp_dir(), DatasetHandler.datasetFileName + ".zip")
    
    @staticmethod
    def __get_dataset_csv_path():
        return os.path.join(StorageHandler.get_data_raw_dir(), DatasetHandler.datasetFileName + ".tsv")

    @staticmethod 
    def download_social_chemstry():
        if not os.path.exists(DatasetHandler.__get_dataset_csv_path()):
            save_zip_path = DatasetHandler.__get_dataset_zip_path()

            gdown.download(id=DatasetHandler.drive_id, output=save_zip_path, quiet=False)

            with zipfile.ZipFile(save_zip_path, 'r') as zipObj:
                zipObj.extractall(StorageHandler.get_data_raw_dir())

    @staticmethod
    def __get_wordnet_pos(tag):
        if tag.startswith('J'):
            return wordnet.ADJ
        if tag.startswith('V'):
            return wordnet.VERB
        if tag.startswith('N'):
            return wordnet.NOUN
        if tag.startswith('R'):
            return wordnet.ADV
        else:
            return ''


    @staticmethod
    def __old_lemmatize(tokens):

        # 
        # download('averaged_perceptron_tagger')
        
        lemmatizer = WordNetLemmatizer()
        pos_tag_dict = dict(pos_tag (tokens)) 
        token_lemmatized = []

        for x in tokens:
            pos = DatasetHandler.__get_wordnet_pos(pos_tag_dict[x])
            if pos == '':
                token_lemmatized.append(x)
            else:
                token_lemmatized.append(lemmatizer.lemmatize(x, pos = pos))

        return token_lemmatized

    @staticmethod
    def __lemmatize(tokens):

        # 
        # download('averaged_perceptron_tagger')
        
        lemmatizer = WordNetLemmatizer()
        pos_tag_dict = dict(pos_tag (tokens)) 
        token_lemmatized = []

        add_subject = False
        first_subject = False
        first_verb = False

        for i in range(len(tokens)):
            x = tokens[i]
            pos = DatasetHandler.__get_wordnet_pos(pos_tag_dict[x])

            if not first_subject and pos_tag_dict[x] == 'PRP':
                first_subject = True

            if not first_verb and pos == wordnet.VERB:
                first_verb = True

                if not first_subject:
                    add_subject = True
            
            if i == 0 and pos == wordnet.VERB:
                add_subject = True

            elif i == 1  and pos == wordnet.VERB and (tokens[0] == "not" or tokens[0] == "Not"):
                add_subject = True
            
            if pos == '':
                token_lemmatized.append(x)
            else:
                token_lemmatized.append(lemmatizer.lemmatize(x, pos = pos))

        token_lemmatized = ['I'] + token_lemmatized if add_subject else token_lemmatized
        token_lemmatized = token_lemmatized + ['.'] if token_lemmatized[-1] != '.' else token_lemmatized


        text = " ".join(token_lemmatized)
        text = text.replace(" ,",",")
        text = text.replace(" .",".")
        text = text.replace("..",".")        
        
        return text

    @staticmethod
    def preprocessing(overwrite = False):

        print("[Preprocessing]")
        if not overwrite:
            df_bad_fred_path = StorageHandler.get_propreccesed_file_path("df_bad_fred.csv")
            df_bad_ValueNet_path = StorageHandler.get_propreccesed_file_path("df_bad_ValueNet.csv")

            df_bad_fred = StorageHandler.load_csv_to_dataframe(df_bad_fred_path)
            df_bad_ValueNet = StorageHandler.load_csv_to_dataframe(df_bad_ValueNet_path)

            if df_bad_fred is not None and df_bad_ValueNet is not None:
                
                print("Load cached files")
                return df_bad_fred, df_bad_ValueNet
            else:
                print("WARNING")
                
        # download('wordnet')
        # stemmer = PorterStemmer()
        df = StorageHandler.load_csv_to_dataframe(DatasetHandler.__get_dataset_csv_path(), sep="\t")

        columns = ['rot-moral-foundations',
            'rot',
            'rot-char-targeting',
            'rot-judgment',
            'action',
            # 'action-char-involved',
            'situation',
            'n-characters', 
            'characters'
        ]

        # drop useless columns
        columns_to_drop = list( set(df.columns) - set(columns) )
        df.drop(columns=columns_to_drop, inplace = True)
        df.dropna(inplace = True)

        pd.set_option("display.max_columns", None)
        print()
        print(f"Dataframe columns: {list(df.columns)}")
        print()
        print(f"Dataframe length: {len(df)}")
        print()
        #-----------------------
        #Split rows when there are more than one diade
        df['rot-judgment'] = df['rot-judgment'].str.lower()#########

        df = df.drop('rot-moral-foundations', axis=1) \
        .join(df['rot-moral-foundations'] \
        .str \
        .split('|', expand=True) \
        .stack() \
        .reset_index(level=1, drop=True).rename('rot-moral-foundations')) \
        .reset_index(drop=True) 
        #-----------------------
        # Filter rows with only bad moral judgment (associated with the correct diade)

        df_mask = df[df['rot-judgment'].str.contains("bad")]
        df_mask = df_mask[~df_mask['rot-judgment'].str.contains("not")]
        df_mask = df_mask[~df_mask['rot-judgment'].str.contains("n't")]

        df_bad = df_mask
        # df_bad = df[df['rot-judgment'].str.contains("not")]
        print("Dataframe \"bad\" length: "+ str(len(df_bad)))
        print()
        print("Dyads: ",df_bad["rot-moral-foundations"].unique().tolist())
        print()

        #Select the correct haidt value associated with "bad" 
        df_bad["haidt-value"] = df_bad["rot-moral-foundations"].apply(lambda x: x.split("-")[1])

        # print(df_bad[["rot-moral-foundations", "haidt-value"]].head())

        #-----------------------
        print("[LEMMATIZATION]")
        # Lemmatization on the reddit thread title called "situation"

        df_bad["situation"] = df_bad["situation"].str.replace("\"","")
        df_bad["situation_lemmatized"]= df_bad["situation"].apply(lambda x: DatasetHandler.__lemmatize(x.split(" ")))
    
        df_bad.drop_duplicates(subset=['rot-moral-foundations','situation_lemmatized'], inplace = True)
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("i be","I am")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("I be","I am")

        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("i not","I don't")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("I not","I don't")


        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("you be","you are")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("You be","You are")

        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("he be","he is")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("He be","He is")

        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("she be","she is")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("She be","She is")

        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("it be","it is")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("It be","It is")

        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("we be","we are")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("We be","We are")
    
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("they be","they are")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("They be","They are")
        
        print()
        print(f"Dataframe \"bad\" length: {len(df_bad)}")
        print()
        #----------------------
        print("[DATAFRAME ANALYSIS]")
        # prepare the csv file for ValueNet
        df_bad_out = pd.DataFrame()
        df_bad_out['text'] = df_bad['situation_lemmatized']
        df_bad_out['label'] = df_bad['haidt-value']

        # analyze the length of text of the whole bad dataset
        # Note: This unique removes the duplicates on the same label (haidt value)
        #       and produces the count of texts for each hait value.
        df_bad_out_grouped = df_bad_out.groupby('label')["text"].nunique()
        
        print()
        print("This Dataframe shows the count of texts for each haidt value.")
        print()
        print(df_bad_out_grouped)
        print()
        
        # Now this dataframe counts texts along labels to analyze the character 
        # length distribution of the text column.
        df_bad_out_uniqued = df_bad_out.drop_duplicates(subset=['text']).reset_index(drop=True)
        df_bad_out_uniqued['text_length'] = df_bad_out_uniqued['text'].apply(lambda x: len(x))

        
        print()
        print("Uniqued data distribution")
        print(df_bad_out_uniqued['text_length'].describe([0.2,0.3,0.4,0.5,0.75,0.99]))
        print()

        print("[CUT RANGE ANALYSIS]")
        # Filter rows with a specific length range and remove duplicates. 
        # Check whether or not the charcater length distribution is preserved.
        # Note: everything that is over 164 is considered as an outliar (1% of data).
        df_bad_out_cutted = df_bad_out[df_bad_out["text"].str.len() >= 60]
        df_bad_out_cutted = df_bad_out_cutted[df_bad_out_cutted["text"].str.len() < 164]

        df_bad_out_grouped_cutted = df_bad_out_cutted.groupby('label')["text"].nunique()
        
        print()
        print(df_bad_out_grouped_cutted)
        print()

        df_bad_out_uniqued_cutted = df_bad_out_cutted.drop_duplicates(subset=['text']).reset_index(drop=True)
        df_bad_out_uniqued_cutted['text_length'] = df_bad_out_uniqued_cutted['text'].apply(lambda x: len(x))

        print()
        print("Uniqued data distribution")
        print(df_bad_out_uniqued_cutted['text_length'].describe([0.2,0.3,0.4,0.5,0.75,0.99]))
        print()

        #----------------------        
        print("[SUMMARY]")
        print()
        print("Base \"bad\" length => uniqued \"bad\" length along labels")
        print("",len(df_bad_out["text"].tolist()), " => ", len(df_bad_out["text"].unique().tolist()))
        print()
        print("Cut \"bad\" length => Cut \"bad\" length uniqued along labels")
        print("",len(df_bad_out_cutted["text"].tolist()), " => ", len(df_bad_out_cutted["text"].unique().tolist()))

        print()
        print("Export csv files")
        StorageHandler.save_data_csv(df_bad_out_uniqued_cutted[["text"]], name="df_bad_fred")
        StorageHandler.save_data_csv(df_bad_out_cutted[["text", "label"]], name="df_bad_ValueNet")

        return df_bad_out_uniqued_cutted[["text"]], df_bad_out_cutted[["text", "label"]]
        
    def retrieve_fred_rdf(df, api_owner, download = True):
        #Retrieve Fred rdfs
        if download:
            StorageHandler.retrieve_text(df["text"].tolist(), api_owner)
            
        
    @staticmethod
    def find_trigs(txt):    
            
        # generate graphs to be used later 

        g_valueObj = rdflib.Graph()
        g_valueSubj = rdflib.Graph()

        g = rdflib.Graph()
        finalg = rdflib.Graph()

        file_hash = txt
        if txt != "out1":
            file_hash = StorageHandler.get_text_hash(txt)

        file_path = StorageHandler.get_rdf_path(file_hash)

        # print(f"FILE PATH: {file_path}")
        cell_graph = g.parse(file_path, format="ttl")

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
        return diz, finalg
    @staticmethod
    def rdf_analysis(df_fred, df_ValueNet):

        error_file = []
        void_ValueNet_response = []
        text_list = df_fred["text"].tolist()


        print()
        print("[RDF ANALYSIS]")
        
        text_list_len = len(text_list)
        for i in range(text_list_len):
        #     file_hash = StorageHandler.get_text_hash(text_list[0])
        #     file_path = StorageHandler.get_rdf_path(file_hash)
        #     g = rdflib.Graph()
        #     result = g.parse(file_path, format='turtle')
            # print(f"text: Someone has to stop that awful killer.")
            
            text = text_list[i]
            print()
            print(f"text [{i}/{text_list_len}]: {text}")
            print()

            try:
                text_dict, turtle_extend = DatasetHandler.find_trigs(text)

                print()
                print("\tSUB:")
                print("\t",text_dict["sub"])
                print()
                print("\tOBJ:")
                print("\t",text_dict["obj"])

                if not (text_dict["sub"] or text_dict["obj"]):
                    void_ValueNet_response.append(text)
                    print("\t No response from ValueNet")

                else:
                    text_hash = StorageHandler.get_text_hash(text)
                    StorageHandler.save_rdf(text_hash, turtle_extend, extended=True)
                    print("\tTurtle extended")
            except:
                print("\tDamaged tutrtle")
                error_file.append(text)

        print()
        print()
        print(f"Total damaged turtles: {len(error_file)}")
        print()
        print(f"Total no response from ValueNet: {len(void_ValueNet_response)}")
        print()

        df_damaged = pd.DataFrame({"text": error_file})
        StorageHandler.save_data_csv(df_damaged, name="df_turtle_damaged")

        df_void = pd.DataFrame({"text": void_ValueNet_response})
        StorageHandler.save_data_csv(df_void, name="df_void_ValueNet_response")

        