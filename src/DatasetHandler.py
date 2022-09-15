from lib2to3.pgen2 import token
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
    def __lemmatize(tokens):

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
    def rdf_analysis(df_fred, df_ValueNet):

        for text in df_fred["text"].tolist():

            file_hash = StorageHandler.get_text_hash(text)
            file_path = StorageHandler.get_rdf_path
            g = rdflib.Graph()
            result = g.parse(file_path, format='turtle')
            
        

    @staticmethod
    def preprocessing():
        
        # download('wordnet')
        # stemmer = PorterStemmer()
        df = StorageHandler.load_csv_to_dataframe(DatasetHandler.__get_dataset_csv_path())

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
        df_bad["situation_lemmatized"]= df_bad["situation"].apply(lambda x: "I " + " ".join(DatasetHandler.__lemmatize(x.split(" "))))
    
        df_bad.drop_duplicates(subset=['rot-moral-foundations','situation_lemmatized'], inplace = True)
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("I be","I am")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("I not","I don't")
        
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

        #Retrieve Fred rdfs
        print()
        print("[DOWNLOADING TURTLE FILES]")
        print()
        StorageHandler.retrieve_text(df_bad_out_uniqued_cutted["text"].tolist())
        print()
        print("[DOWNLOADING TURTLE FILES COMPLETED]")

        return df_bad_out_uniqued_cutted[["text"]], df_bad_out_cutted[["text", "label"]]
        
        