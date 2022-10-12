from StorageHandler import StorageHandler
from Statistic import Statistic

from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from nltk.corpus import wordnet

import pandas as pd
import gdown
import zipfile
import os
import rdflib

import requests
import rdflib
from rdflib import Namespace, URIRef
import SPARQLWrapper
from SPARQLWrapper import SPARQLWrapper, JSON, N3, TURTLE, RDF, CSV
import json
import os
import pandas as pd

import numpy as np

'''

ipotesi: Harm è una superclasse rispetto a tutti (o quasi) gli altri valori di haidt
ipotesi: Harm è troppo generica => non fornisce informazioni utili nell'embedding space
'''
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
turtleNet = SPARQLWrapper('http://localhost:3030/turtle_analysis/sparql')

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

primary_role = [
    "Agent",
    "Actor",
    "Beneficiary",
    "Cause",
    "Experiencer",
    "Patient",
    "Recipient",
    "Theme",
    "Toward"
]

secondary_role = [
    "Abstract_or_physical",
    "Actor1",
    "Actor2",
    "Agent_i",
    "Agent_j",
    "Asset",
    "Attribute",
    "Destination",
    "Directedmotion",
    "Direction",
    "During_Event",
    "During_Event1",
    "During_Event2",
    "Emotion",
    "End_Event",
    "End_Event1",
    "End_Event2",
    "Endstate",
    "Event",
    "Event1",
    "Event2",
    "Extent",
    "Forceful",
    "Form",
    "From",
    "Illegal",
    "Instrument",
    "Location",
    "Location1",
    "Location2",
    "Material",
    "Motion",
    "Oblique",
    "Oblique1",
    "Odor",
    "Patient1",
    "Patient1_or_Patient2",
    "Patient2",
    "Physical",
    "Physical_or_Abstract",
    "Pivot",
    "Pos",
    "Predicate",
    "Prep_Dir",
    "Product",
    "Prop",
    "Proposition",
    "Result",
    "Result_Event",
    "Role",
    "Sound",
    "Source",
    "Start_Event",
    "Start_Event1",
    "Start_Event2",
    "Stimulus",
    "Theme1",
    "Theme2",
    "Time",
    "Topic",
    "Value",
    "Weather_type"

]

complex_haidt_dict = {
            "francinelock" : "lock",
            "massagetherapist" : "therapist",
            "finderkeeper" : "keeper",
            "notedchildkidnapper" : "kidnapper",
            "sociopathictendency" : "sociopathic",
            "mentaldisability" : "disability",
            "icompletelyannihilate" : "annihilate",
            "accidentallybump" : "bump",
            "passengerseat": "seat",
            "newtoiletseat": "seat",
            "hugepatch": "patch",
            "soulpatch": "patch"
        }

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
        if tag.startswith('V') or tag.startswith('MD'):
            return wordnet.VERB
        if tag.startswith('N'):
            return wordnet.NOUN
        if tag.startswith('R'):
            return wordnet.ADV
        else:
            return ''

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

            if not first_subject and (pos_tag_dict[x].startswith('PRP') or pos_tag_dict[x].startswith('NN')):
                first_subject = True

            if not first_verb and pos == wordnet.VERB:
                first_verb = True

                if not first_subject:
                    add_subject = True
            
            if i == 0 and pos == wordnet.VERB:
                add_subject = True
                tokens[i] = tokens[i].lower()

            elif i == 1  and pos == wordnet.VERB and (tokens[0] == "not" or tokens[0] == "Not"):
                add_subject = True
            
            if pos == '':
                token_lemmatized.append(x)
            else:
                token_lemmatized.append(lemmatizer.lemmatize(x, pos = pos))

        token_lemmatized = ['I'] + token_lemmatized if add_subject else token_lemmatized
        token_lemmatized = token_lemmatized + ['.'] if token_lemmatized[-1] != '.' else token_lemmatized
        token_lemmatized[0] = token_lemmatized[0].title()

        text = " ".join(token_lemmatized)
        text = text.replace(" ,",",")
        text = text.replace(" .",".")
        text = text.replace("..",".")        
        
        return text

    @staticmethod
    def expand_text(df, col_name):
        # "situation_lemmatized"
        df[col_name] = df[col_name].str.replace("i be","I am")
        df[col_name] = df[col_name].str.replace("I be","I am")

        df[col_name] = df[col_name].str.replace("i'm","I am")
        df[col_name] = df[col_name].str.replace("I'm","I am")

        df[col_name] = df[col_name].str.replace("i've","I have")
        df[col_name] = df[col_name].str.replace("I've ","I have")

        df[col_name] = df[col_name].str.replace("i'd","I would")
        df[col_name] = df[col_name].str.replace("I'd","I would")

        df[col_name] = df[col_name].str.replace("i not","I don't")
        df[col_name] = df[col_name].str.replace("I not","I don't")

        df[col_name] = df[col_name].str.replace("you be","you are")
        df[col_name] = df[col_name].str.replace("You be","You are")

        df[col_name] = df[col_name].str.replace("you're","you are")
        df[col_name] = df[col_name].str.replace("You're","You are")

        df[col_name] = df[col_name].str.replace("you've","you have")
        df[col_name] = df[col_name].str.replace("You've ","You have")

        df[col_name] = df[col_name].str.replace("you'd","you would")
        df[col_name] = df[col_name].str.replace("You'd","You would")

        df[col_name] = df[col_name].str.replace("he be","he is")
        df[col_name] = df[col_name].str.replace("He be","He is")

        df[col_name] = df[col_name].str.replace("he's","he is")
        df[col_name] = df[col_name].str.replace("He's","he is")

        df[col_name] = df[col_name].str.replace("he'd","he would")
        df[col_name] = df[col_name].str.replace("He'd","He would")

        df[col_name] = df[col_name].str.replace("it be","it is")
        df[col_name] = df[col_name].str.replace("It be","It is")

        df[col_name] = df[col_name].str.replace("it's","it is")
        df[col_name] = df[col_name].str.replace("It's","It is")

        df[col_name] = df[col_name].str.replace("it'd","it would")
        df[col_name] = df[col_name].str.replace("It'd","It would")

        df[col_name] = df[col_name].str.replace("we be","we are")
        df[col_name] = df[col_name].str.replace("We be","We are")

        df[col_name] = df[col_name].str.replace("we're","we are")
        df[col_name] = df[col_name].str.replace("We're","We are")

        df[col_name] = df[col_name].str.replace("we've","we have")
        df[col_name] = df[col_name].str.replace("We've ","We have")

        df[col_name] = df[col_name].str.replace("we'd","we would")
        df[col_name] = df[col_name].str.replace("We'd","We would")

        df[col_name] = df[col_name].str.replace("they be","they are")
        df[col_name] = df[col_name].str.replace("They be","They are")

        df[col_name] = df[col_name].str.replace("they're","they are")
        df[col_name] = df[col_name].str.replace("They're","They are")

        df[col_name] = df[col_name].str.replace("they've","they have")
        df[col_name] = df[col_name].str.replace("They've ","They have")

        df[col_name] = df[col_name].str.replace("they'd","they would")
        df[col_name] = df[col_name].str.replace("They'd","They would")

        return df

    @staticmethod
    def preprocessing(overwrite = False):

        print("[Preprocessing]")
        if not overwrite:
            df_bad_fred_path = StorageHandler.get_propreccesed_file_path("df_bad_fred.csv")
            df_bad_ValueNet_path = StorageHandler.get_propreccesed_file_path("df_bad_ValueNet.csv")

            df_bad_fred = StorageHandler.load_csv_to_dataframe(df_bad_fred_path)
            df_bad_ValueNet = StorageHandler.load_csv_to_dataframe(df_bad_ValueNet_path)

            if df_bad_fred is not None and df_bad_ValueNet is not None:
                
                print("\tLoading cached files")

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

        dyads_bad = df_bad["rot-moral-foundations"].unique().tolist()
        print("Dataframe \"bad\" length: "+ str(len(df_bad)))
        print()
        print("Dyads: ",dyads_bad)
        print()

        #Select the correct haidt value associated with "bad" 

        df_bad["haidt-value"] = df_bad["rot-moral-foundations"].apply(lambda x: x.split("-")[1])
        # df_bad['rot-moral-foundations'] = df_bad['rot-moral-foundations'].apply(lambda x: x.split("|"))
        # df_bad['haidt-value'] = df_bad['rot-moral-foundations'].apply(lambda x: [el.split("-")[1] for el in x])

        # print(df_bad[["rot-moral-foundations", "haidt-value"]].head())

        #-----------------------
        print("[LEMMATIZATION]")
        # Lemmatization on the reddit thread title called "situation"

        df_bad["situation"] = df_bad["situation"].str.replace("\"","")
        df_bad = DatasetHandler.expand_text(df_bad, "situation")
        df_bad["situation_lemmatized"]= df_bad["situation"].apply(lambda x: DatasetHandler.__lemmatize(x.split(" ")))
        df_bad = DatasetHandler.expand_text(df_bad, "situation_lemmatized")

        df_bad.drop_duplicates(subset=['rot-moral-foundations',"situation_lemmatized"], inplace = True)

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
        df_bad_out_cutted = df_bad_out[df_bad_out["text"].str.len() >= 59]
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


        df_bad_ValueNet = df_bad_out_cutted[["text", "label"]]
        df_bad_ValueNet = df_bad_ValueNet.groupby('text').agg({'text' : 'first', 'label' : ' '.join}).reset_index(drop=True)

        print("Export csv files")
        StorageHandler.save_data_csv(df_bad_out_uniqued_cutted[["text"]], name="df_bad_fred")

        # StorageHandler.save_data_csv(df_bad_out_cutted[["text", "label"]], name="df_bad_ValueNet")
        # return df_bad_out_uniqued_cutted[["text"]], df_bad_out_cutted[["text", "label"]]

        StorageHandler.save_data_csv(df_bad_ValueNet, name="df_bad_ValueNet")

        print(len(df_bad_ValueNet)," - ", len(df_bad_out_uniqued_cutted[["text"]]))
        return df_bad_out_uniqued_cutted[["text"]], df_bad_ValueNet
        
    def retrieve_fred_rdf(df, api_owner, download = True):
        #Retrieve Fred rdfs
        if download:
            StorageHandler.retrieve_text(df["text"].tolist(), api_owner)
            
        
    @staticmethod
    def find_trigs(cell_graph):    
            
        # generate graphs to be used later 

        g_valueObj = rdflib.Graph()
        g_valueSubj = rdflib.Graph()

        finalg = rdflib.Graph()

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
    def __remove_NameSpaces(data, namespace):
        data = [
        ele.replace(namespace,'').strip().lower() 
            for ele in 
                data
        ]

        return data

    @staticmethod
    def get_ValueNet_results(text_dict):
        prediction = list(set([str(ele) for ele in text_dict['obj']]))
        # prediction = DatasetHandler.__remove_NameSpaces(prediction, 'https://w3id.org/spice/SON/HaidtValues#')

        prediction = [el.split("#")[-1] for el in prediction]

        triggers = list(set([str(ele) for ele in text_dict['sub']]))
        # triggers = DatasetHandler.__remove_NameSpaces(triggers, 'https://w3id.org/framester/wn/wn30/instances')
        # triggers = DatasetHandler.__remove_NameSpaces(triggers, 'https://w3id.org/framester/vn/vn31/data')

        triggers = [el.split("/")[-1] for el in triggers]

        return prediction, triggers

    @staticmethod
    def retrieve_ValueNet_data(df_ValueNet, overwrite=True):
        print()
        print("[RDF LABELS-TRIGGERS]")
        
        if not overwrite:
            file_path = StorageHandler.get_propreccesed_file_path("df_ValueNet_response.csv")
            df_ValueNet = StorageHandler.load_csv_to_dataframe(file_path)
            print()
            print("\tLoading cached file")

        else:
            assert df_ValueNet is not None

            haidt_predictions = []
            triggers = []

            error_file = []
            void_ValueNet_response = []

            text_list = df_ValueNet["text"].tolist()
            text_list_len = len(text_list)

            text_log = []

            is_ok = True

            for i in range(text_list_len):
                if not is_ok:
                    break

                text = text_list[i]
                
                print()
                print(f"text [{i}/{text_list_len}]: {text}")
                print()

                try:
                    text_hash = StorageHandler.get_text_hash(text)
                    file_path = StorageHandler.get_rdf_path(text_hash)

                    g = rdflib.Graph()
                    cell_graph = g.parse(file_path, format="ttl")

                    try:
                        text_dict, turtle_extend = DatasetHandler.find_trigs(cell_graph)

                        if not (text_dict["sub"] or text_dict["obj"]):
                            void_ValueNet_response.append(text)
                            haidt_predictions.append("<no response>")
                            triggers.append("<no response>")
                            print("\t No response from ValueNet")
            
                        else:

                            text_hash = StorageHandler.get_text_hash(text)
                            StorageHandler.save_rdf(text_hash, turtle_extend, extended=True)
                            print("\tTurtle extended")

                            text_path = StorageHandler.get_rdf_path(text_hash, extended=True)
                            info_dict = {}
                            info_dict["text"] = text
                            info_dict["hash"] = text_hash
                            info_dict["saved"] = os.path.exists(text_path)

                            text_log.append(info_dict)

                            prediction, text_triggers = DatasetHandler.get_ValueNet_results(text_dict)

                            haidt_predictions.append(" ".join(prediction))
                            triggers.append(" ".join(text_triggers))

                    except:
                        print()
                        print("[ERROR] ValueNet server is not working")
                        print()
                        is_ok = False
                        # break
                except:
                    print("\tDamaged turtle")
                    haidt_predictions.append("<damaged>")
                    triggers.append("<damaged>")
                    error_file.append(text)

            if is_ok:
                error_file_length = len(error_file)
                no_response_length = len(void_ValueNet_response)
                StorageHandler.save_json("file_info.json", text_log)
                
                print()
                print()
                print(f"Total damaged turtles: {error_file_length}")
                print()
                print(f"Total no response from ValueNet: {no_response_length}")
                print()
                print(f"Total extended turtle: {text_list_len - no_response_length - error_file_length}")
                print()

                df_damaged = pd.DataFrame({"text": error_file})
                StorageHandler.save_data_csv(df_damaged, name="df_turtle_damaged")

                df_void = pd.DataFrame({"text": void_ValueNet_response})
                StorageHandler.save_data_csv(df_void, name="df_void_ValueNet_response")

                df_ValueNet["label_predicted"] = haidt_predictions
                df_ValueNet["label_triggers"] = triggers


                df_ValueNet["label"] = df_ValueNet["label"].str.lower()
                df_ValueNet["label_predicted"] = df_ValueNet["label_predicted"].str.lower()
                df_ValueNet["label_triggers"] = df_ValueNet["label_triggers"].str.lower()

                StorageHandler.save_data_csv(df_ValueNet, name="df_ValueNet_response")

        return df_ValueNet, is_ok

    @staticmethod
    def build_haidt_dict(df, show=False):
        def __populate(data_dict, src, values, out_filename):
            assert src == "label" or src == "trigger"

            if src == "label":
                column_name = "label_predicted"
            else:
                column_name = "label_triggers"

            column_predicted = df[~df[column_name].str.contains("<damaged>")]
            column_predicted = column_predicted[~column_predicted[column_name].str.contains("<no response>")][column_name].tolist()

            for value, data in tuple(zip(values, column_predicted)):
                value_split = value.split(" ")
                for el in value_split:
                    data_dict[el] = data_dict[el] + data.split(" ")

            for key in label_dict.keys():
                data_dict[key] = list(np.unique(data_dict[key]))



            if src == "trigger":
                for key in label_dict.keys():
                    data_dict[key] = [el.split("_")[0] for el in data_dict[key]]
                    data_dict[key] = ["-".join(el.split("-")[1:]) if "-" in el else el for el in data_dict[key]]

            if show:
                print(f"[{src}]")
                print()

                for key in label_dict.keys():
                    print(f"\t{key} : {data_dict[key]}")
                
                print()
                print(f"[Saving {src}]")
                print()
                StorageHandler.save_json(out_filename, data_dict)

            return data_dict

        haidt_values = df["label"].tolist()
        haidt_values = [value for el in haidt_values for value in el.split(" ")]
        haidt_values = np.array(haidt_values)
        haidt_values = list(np.unique(haidt_values))

        label_dict = {}
        trigger_dict = {}

        for value in haidt_values:
            label_dict[value] = []
            trigger_dict[value] = []

        values = df["label"].tolist()

        label_dict = __populate(label_dict, "label", values, "label_predicted.json")
        trigger_dict = __populate(trigger_dict, "trigger", values, "trigger_predicted.json")

        return label_dict, trigger_dict

            

    @staticmethod
    def build_count(row, count_dict, haidt_response_partition):
        labels_true = row["label"].split(" ")
        labels_predicted = row["label_predicted"].split(" ")

        # print(f"{labels_true} -> {labels_predicted}")

        count = 0

        for label in labels_true:
            if label in labels_predicted:
                count += 1
                count_dict[label]["count"] += 1
                count_dict[label]["percentage"] = round(count_dict[label]["count"] / haidt_response_partition[label],2) * 100
        row["label_count_matched"] = count

        return row


    @staticmethod 
    def print_dict(mydict, level = 0):
        parsed = json.loads(str(mydict).replace("'","\""))
        print("".join(["\t" for _ in range(level)]),"",json.dumps(parsed, indent=4))

    @staticmethod
    def rdf_statistical_analysis(df_ValueNet, overwrite = True):
        print("[RDF STATISTICAL ANALYSIS]")
        df_name = "df_ValueNet_statistics"

        if not overwrite:
            df_path = StorageHandler.get_propreccesed_file_path(df_name+".csv")
            df_ValueNet = StorageHandler.load_csv_to_dataframe(df_path)

            if df_ValueNet is not None:
                print("\t[Error] Dataframe not found")
            else:
                print("\tusing cached file")
            return df_ValueNet

        damaged_count = df_ValueNet[df_ValueNet["label_predicted"].str.contains("<damaged>")]["label_predicted"].count()
        df_ValueNet = df_ValueNet[~df_ValueNet["label_predicted"].str.contains("<damaged>")]

        no_response_count = df_ValueNet[df_ValueNet["label_predicted"].str.contains("<no response>")]["label_predicted"].count()
        df_ValueNet = df_ValueNet[~df_ValueNet["label_predicted"].str.contains("<no response>")]

        haidt_values = df_ValueNet["label"].tolist()
        haidt_values = [value for el in haidt_values for value in el.split(" ")]
        haidt_values = np.array(haidt_values)
        haidt_values = list(np.unique(haidt_values))

        haidt_values_pred = df_ValueNet["label_predicted"].tolist()
        haidt_values_pred = [value for el in haidt_values_pred for value in el.split(" ")]
        haidt_values_pred = np.array(haidt_values_pred)
        haidt_values_pred = list(np.unique(haidt_values_pred))

        print("haidt values")
        print(haidt_values)
        print()
        # print("haidt values predicted")
        # print(haidt_values_pred)
        # print()


        df_ValueNet["label_count"] = df_ValueNet["label"].apply(lambda x: len(x.split(" ")))
        
        print("Social Chemistry label distribution")
        print(df_ValueNet["label_count"].describe(np.linspace(0.1,1.0,10).tolist()))
        print()

        df_ValueNet["label_predicted_count"] = df_ValueNet["label_predicted"].apply(lambda x: len(x.split(" ")))
        print("ValueNet label predicted distribution")
        print(df_ValueNet["label_predicted_count"].describe(np.linspace(0.1,1.0,10).tolist()))
        print()

        print("Social Chemistry haidt value count: ", df_ValueNet["label_count"].sum())
        print("ValueNet predictions", df_ValueNet["label_predicted_count"].sum())

        count_dict = dict(zip(haidt_values,([{"count":0, "percentage": 0} for i in range(len(haidt_values))])))
        haidt_response_partition = {}

        for value in haidt_values:
            haidt_response_partition[value] = df_ValueNet[df_ValueNet["label"].str.contains(value)]["label"].count()

        response_count = sum(list(haidt_response_partition.values()))
        response_raw_count =len(df_ValueNet)
        print()
        print(f"Fred damaged response: {damaged_count}")
        print(f"ValueNet no response: {no_response_count}")
        print(f"ValueNet haidt raw response count: {response_raw_count} ")
        print(f"ValueNet haidt response repetition: {response_count}")

        print("ValueNet haidt partion response")
        DatasetHandler.print_dict(haidt_response_partition)
        print()

        df_ValueNet = df_ValueNet.apply(lambda x: DatasetHandler.build_count(x, count_dict, haidt_response_partition), axis=1)

        print("ValueNet correct prediction")
        DatasetHandler.print_dict(count_dict)
        print()

        
        correct_response_count = [ el["count"] for el in count_dict.values()]
        correct_response_count = sum(correct_response_count)
        print("Total percentage: ", round(correct_response_count / response_count,2) * 100)
        print()
        # label_dict, trigger_dict = DatasetHandler.build_haidt_dict(df_ValueNet, show=True)

        StorageHandler.save_data_csv(df_ValueNet, name=df_name)
        print("\tdataframe saved")
        return df_ValueNet

    @staticmethod
    def trigger_query(graph):

        global prefixes

        query =prefixes +"SELECT ?s ?s_o ?o ?v\
                        WHERE{ ?s ?p ?o .\
                        ?o vcvf:triggers ?v .\
                        ?s rdfs:subClassOf ?s_o\
                        }"

        res = graph.query(query)
        res_list=[]
        for row in res:
            row_dict = {}

            row_dict["subject"] = str(row.s)
            row_dict["subject_subClassOf"] = str(row.s_o)
            row_dict["trigger"] = str(row.o)
            row_dict["trigger_value"] = str(row.v)
            # row_dict["s"] = str(row.s)
            # row_dict["s superClass"] = str(row.s_o)
            # row_dict["s trigger"] = str(row.s_oo)
            # row_dict["o"] = str(row.o)
            # row_dict["v"] = str(row.v)
            # row_dict["p"] = str(row.p)

            res_list.append(row_dict)
        
        return res_list

    @staticmethod
    def __path_query(role, intermediate_nodes = 0, role_start = "obj"):
        global prefixes

        assert intermediate_nodes >= 0
        assert role_start == "sub" or role_start == "obj"
   
        
        query = ""

        if role_start == "obj":

            query = "?o_c0 "
            query += " ".join(["?o_c"+str(i+1) for i in range(intermediate_nodes)])
            query = prefixes + " SELECT "+ query + " ?v WHERE{ "
            query += "?s ns1:"+role+" ?o. "
            query += "?o rdf:type ?o_c0. "
            query += " ".join(["?o_c"+str(i)+" rdfs:subClassOf ?o_c"+str(i+1)+". " for i in range(intermediate_nodes)])
            query += "?o_c"+str(intermediate_nodes)+" vcvf:triggers ?v"
            query +="}"

        else:

            query = "?s_c0 "
            query += " ".join(["?s_c"+str(i+1) for i in range(intermediate_nodes)])
            query = prefixes + " SELECT "+ query + " ?v WHERE{ "
            query += "?s ns1:"+role+" ?o. "

            query += "?s rdf:type ?s_c0. "
            query += " ".join(["?s_c"+str(i)+" rdfs:subClassOf ?s_c"+str(i+1)+". " for i in range(intermediate_nodes)])
            query += "?s_c"+str(intermediate_nodes)+" vcvf:triggers ?v"
            query +="}"

        return query


    @staticmethod
    def __remove_local_cycle(l,i, cleaned_l):
        if i >= len(l):
            return

        if l.index(l[i]) == i:
            cleaned_l.append(l[i])
        else:
            prev_index = l.index(l[i])
            s_l = l[:prev_index]
            cleaned_l[:] = s_l + [l[i]]
        
        DatasetHandler.__remove_local_cycle(l,i+1, cleaned_l)


    @staticmethod
    def __check_path(path_dict, visited_paths: list):

        path = [ el["value"] for el in path_dict.values()]

        is_ok = True
        
        # for i in range(len(path)):

        for v_path in visited_paths:
            if " ".join(v_path) in " ".join(path):
                is_ok = False
                break
    
        
        if is_ok:
        
            cleaned_path = []
            DatasetHandler.__remove_local_cycle(path,0,cleaned_path)

            if cleaned_path not in visited_paths:
                visited_paths.append(cleaned_path)
            else:
                is_ok = False

        return is_ok, visited_paths


    """
    A -> B -> C -> D -> B -> C -> D -> F 
    A -> B -> C -> D -> B -> C -> D -> B -> C -> D -> F 
    -------------------------------
    A -> B -> F
    A -> B -> D -> F
    A -> B -> C -> D -> F

    A -> Z -> X -> Z -> X -> F =>     A -> Z -> X -> F
    A -> Z -> X -> Z -> X -> F
    """

    # (1) - (3) - (4)
    @staticmethod
    def path_analysis(df_ValueNet, role_start = "obj", df_concatenate = False, overwrite = True, fuseki = True):

        print("\t[Path analysis]")
        
        if not overwrite:

            df_file_path = StorageHandler.get_propreccesed_file_path("df_path_info.csv")
            df_file = StorageHandler.load_csv_to_dataframe(df_file_path)

            if df_file is None:
                print("\t\t[ERROR] No previous path_info.csv found")
            else:
                print("\t\tCached dataframe loaded")
            
            json_file = dict(StorageHandler.load_json("average_path.json"))

            if not json_file:
                print("\t\t[ERROR] No previous average_path found")
            else:
                print("\t\tCached json loaded")

            return json_file, df_file

        local_turtleNet = rdflib.Graph()
        
        if not fuseki:
            texts = df_ValueNet["text"].tolist()

            for text in texts:

                graph = StorageHandler.load_rdf(text, extended=True)
                if graph is not None: 
                    for s, p, o in graph.triples((None, None, None)):
                        s = str(s)
                        p = str(p)
                        o = str(o)
                        local_turtleNet.add((URIRef(s), URIRef(p), URIRef(o)))

            print("\t\tLoaded local turtleNet")

        roles = primary_role  + secondary_role 
        role_dict = {role:[] for role in roles}
        visited_paths = []
        df_dict = {"role":[], "role_start": [], "haidt":[], "path":[]}

        print("\t\t Path analysis for role "+("subject" if role_start == "sub" else "object"))

        for role in roles:
            i = 0
            # result = []

            while True:
                query = DatasetHandler.__path_query(role, intermediate_nodes=i, role_start=role_start)
                
                result = None
                if fuseki:
                    
                    turtleNet.setQuery(query)
                    turtleNet.setReturnFormat(JSON)
                    data = turtleNet.query().convert()

                    results = data["results"]["bindings"]

                else:
                    data = local_turtleNet.query(query)
                    results = data.bindings

                #########

                cleaned_result = [] 


                for path in results:

                    if not fuseki:
                        path_keys = [str(el) for el in list(path.keys())]
                        path_values = [{'type':'uri', 'value': str(el)} for el in list(path.values())]
                        path = dict(zip(path_keys, path_values))

                    is_ok, visited_paths = DatasetHandler.__check_path(path, visited_paths)
                    if is_ok:
                        cleaned_result.append(path)

                results = cleaned_result   
                ########

                if len(results) > 0 or i == 0:  
                    role_dict[role].append(len(results))

                    print()
                    print(f"\t\t\t{role}-{i}: {len(results)}")        

                    # get_path = lambda x: " ".join([el["value"].split("/")[-1] for el in x.values()])
                    get_path = lambda x: [el["value"] for el in x.values()]
                    
                    for result in results:
                        # haidt = result["v"]["value"].split("/")[-1]
                        haidt = result["v"]["value"].split("#")[-1]
                        path = get_path(result)

                        df_dict["role"].append(role)
                        df_dict["role_start"].append(role_start)
                        df_dict["haidt"].append(haidt)
                        df_dict["path"].append(" ".join(path))

                    i += 1
                else:
                    break

            role_dict[role] = sum(role_dict[role])/len(role_dict[role])

        df_path = pd.DataFrame(df_dict)
        json_file = {role_start: role_dict}

        if df_concatenate:
            df_file_path = StorageHandler.get_propreccesed_file_path("df_path_info.csv")
            df_file = StorageHandler.load_csv_to_dataframe(df_file_path)

            if df_file is not None:
                df_path = pd.concat([df_file, df_path]).reset_index(drop=True)

            else:
                print("\t\t[ERROR] No previous path_info.csv found")
                return role_dict, df_path
            
            json_file = dict(StorageHandler.load_json("average_path.json"))

            if not json_file:
                print("\t\t[ERROR] No previous average_path found")
                return role_dict, df_path
            
            json_file[role_start] = role_dict


        StorageHandler.save_data_csv(df_path, name="df_path_info")
        print("\t\tDataframe saved")

        StorageHandler.save_json("average_path.json", json_file)
        print("\t\tJson file saved")

        return json_file, df_path


    @staticmethod
    def __is_verbnet(uri):
        return True if "vn" == uri.split(":")[0] else False

    def __is_wordnet(uri):
        
        return True if "synset" in uri.split(":")[1] else False

    def __is_frame(uri):
        return True if "https://w3id.org/framester/data/framestercore/" in uri else False

    # (2)
    @staticmethod
    def trigger_info(df_ValueNet, overwrite = True):
        json_file = "triggers_group.json"

        print("\t[Trigger groups]")
        if not overwrite:
            json_path = StorageHandler.get_propreccesed_file_path(json_file)
            triggers_dict = dict(StorageHandler.load_json(json_path))

            if not triggers_dict:
                print("\t\t[ERROR] Json file not found")
            else:
                print("\t\tCached file loaded")

            return triggers_dict
        
        global prefixes

        query = prefixes + "SELECT ?s ?o WHERE \
                {\
                ?s vcvf:triggers ?o.\
                }"

        triggers_dict = {
            "verbnet": 0,
            "wordnet": 0,
            "frame": 0,
            "other": 0
        }

        for text in df_ValueNet["text"].tolist():
            try:
                # print(text)
                graph = StorageHandler.load_rdf(text, extended=True)
                res = graph.query(query)
                subs = [graph.qname(el) for el in list(dict(res).keys())]
                # print(f"{subs}")

                for sub in subs:
                    if DatasetHandler.__is_verbnet(sub):
                        triggers_dict["verbnet"] += 1
                    elif DatasetHandler.__is_wordnet(sub):
                        triggers_dict["wordnet"] += 1
                    elif DatasetHandler.__is_frame(sub):
                        triggers_dict["frame"] += 1
                    else:
                        triggers_dict["other"] += 1
            except:
                print("\t\t[ERROR] Unable to run the query")
                break

        DatasetHandler.print_dict(triggers_dict)

        StorageHandler.save_json(json_file, triggers_dict)
        print("\t\tJson file saved")
        return triggers_dict

    @staticmethod
    def get_path_embedding(path):

        global complex_haidt_dict
        first = path.split(" ")[0]
        token = first.split("#")[-1].lower()
        
        lemmatizer = WordNetLemmatizer()
        pos_tag_dict = dict(pos_tag ([token]))
        pos = DatasetHandler.__get_wordnet_pos(pos_tag_dict[token])

        token = lemmatizer.lemmatize(token, pos = pos)

        embd = [0]*int(StorageHandler.glove_ver)
        
        try:
            embd = StorageHandler.glove[token]
        except:
            
            if token in complex_haidt_dict.keys():
                embd = StorageHandler.glove[complex_haidt_dict[token]]
                print(f"[Warning] Unknown {token} -> resolved ")
            else:
                print(f"[ERROR] {token}")

        return embd


    @staticmethod
    def build_pca_dict(df):
        global complex_haidt_dict
        haidt_dict = {}

        haidt_values = df["haidt"].unique().tolist()
        
        for value in haidt_values:
            df_value = df[df["haidt"] == value]
            paths = df_value["path"].tolist()
            words = [path.split(" ")[0] for path in paths]
            words = [word.split("#")[-1] for word in words]
            words = [word.lower() for word in words]
            words = [
                complex_haidt_dict[word] if word in complex_haidt_dict.keys() else word 
                for word in words
            ]

            haidt_dict[value] = words
            
        # DatasetHandler.print_dict(haidt_dict)
        return haidt_dict

    @staticmethod
    def rdf_semantic_analysis(df_ValueNet, overwrite=False):

        print("[Semantic analysis]")

        trigger_dict = DatasetHandler.trigger_info(df_ValueNet, overwrite=overwrite)
        df_role = None
        role_dict = None

        if not overwrite:
            role_dict, df_role = DatasetHandler.path_analysis(df_ValueNet, overwrite=False)
        else:

            DatasetHandler.path_analysis(df_ValueNet,role_start="obj", fuseki=False)
            
            role_dict, df_role = DatasetHandler.path_analysis(df_ValueNet, role_start="sub", df_concatenate=True, fuseki=False)

            
        df_role_grouped = df_role.groupby(["role","haidt","role_start"]).nunique()

        print()
        print(df_role_grouped)
        print()

        df_role_grouped = df_role_grouped.reset_index(["role","haidt","role_start"])

        df_role_grouped = df_role_grouped.rename(columns = {"path": "occurences"})

        StorageHandler.save_data_csv(df_role_grouped, name="df_path_relation_info")

        df_role["start_embedding"] = df_role["path"].apply(lambda x: DatasetHandler.get_path_embedding(x)) 
        df_role["haidt_embedding"] = df_role["haidt"].apply(lambda x: DatasetHandler.get_path_embedding(x)) 


        haidt_dict = DatasetHandler.build_pca_dict(df_role)
        Statistic.plot_haidt_embeddings(StorageHandler.glove, haidt_dict)




            




    @staticmethod
    def trash():
        pass
            # texts = df_ValueNet["text"].tolist()

            # for text in texts:
            #     print()
            #     print(f"text: {text}")

            #     graph = StorageHandler.load_rdf(text, extended=True)
            #     if graph is not None: 
            #         # res = DatasetHandler.trigger_query(graph)
            #         # for data in res:
            #         #     print()
            #         #     DatasetHandler.print_dict(data)

            #         res = DatasetHandler.role_query(graph)
            #         DatasetHandler.print_dict(res)
            #         # break
                    

    # useless?
    @staticmethod
    def role_query(graph):

        global prefixes
        global primary_role
        global secondary_role

        roles = primary_role  + secondary_role 
        role_dict = {role:[] for role in roles}
        # role_dict = {"ALL":[]}

        for role in roles:
            query =prefixes +"SELECT ?s4 ?s3 ?p3 ?s2 ?p2 ?s1 ?p1 ?trigger ?trigger_value\
	                        WHERE{\
		                    ?trigger vcvf:triggers ?trigger_value.\
                            ?s1 ?p1 ?trigger.\
                            ?s2 ?p2 ?s1.\
                            ?s3 ?p3 ?s2.\
                            ?s4 ns1:"+role+" ?s3\
	                        }"
                                # ?s rdfs:equivalentClass ?s_c.\
                                #?s vcvf:triggers ?v .\

            res = graph.query(query)
            # print(query)

            for row in res:
                row_dict = {}

                row_dict["s4"] = str(row.s4)
                row_dict["s3"] = str(row.s3)
                row_dict["p3"] = str(row.p3)
                row_dict["s2"] = str(row.s2)
                row_dict["p2"] = str(row.p2)
                row_dict["s1"] = str(row.s1)
                row_dict["p1"] = str(row.p1)
                row_dict["trigger"] = str(row.trigger)
                row_dict["trigger_value"] = str(row.trigger_value)


                role_dict[role].append(row_dict)
            # break
            
        return role_dict
                

        

        