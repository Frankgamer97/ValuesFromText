from lib2to3.pgen2 import token
from StorageHandler import StorageHandler

from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag, download
from nltk.corpus import wordnet

import pandas as pd
import gdown
import zipfile
import os

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


        columns_to_drop = list( set(df.columns) - set(columns) )
        df.drop(columns=columns_to_drop, inplace = True)
        df.dropna(inplace = True)

        pd.set_option("display.max_columns", None)
        print()
        print(df.head())
        print()
        print(len(df))
        print()
        print(df.columns)
        print()

        df['rot-judgment'] = df['rot-judgment'].str.lower()


        # df['rot-judgment'] = df['rot-judgment'].str.replace("it's ","")

        # print(df['rot-judgment'].unique().tolist())
        # print(len(df['rot-judgment'].unique().tolist()))

        df = df.drop('rot-moral-foundations', axis=1) \
        .join(df['rot-moral-foundations'] \
        .str \
        .split('|', expand=True) \
        .stack() \
        .reset_index(level=1, drop=True).rename('rot-moral-foundations')) \
        .reset_index(drop=True) 


        df_mask = df[df['rot-judgment'].str.contains("bad")]
        df_mask = df_mask[~df_mask['rot-judgment'].str.contains("not")]
        df_mask = df_mask[~df_mask['rot-judgment'].str.contains("n't")]

        df_bad = df_mask
        # df_bad = df[df['rot-judgment'].str.contains("not")]
        print("it's bad: "+ str(len(df_bad)))
        print()
        print(df_bad["rot-moral-foundations"].unique().tolist())
        print()
        # print()
        # for el in df_bad["rot-judgment"].unique().tolist():
        #     print(el)
        # print()


        #label column 
        df_bad["haidt-value"] = df_bad["rot-moral-foundations"].apply(lambda x: x.split("-")[1])

        print(df_bad[["rot-moral-foundations", "haidt-value"]].head())

        df_bad["situation"] = df_bad["situation"].str.replace("\"","")
        df_bad["situation_lemmatized"]= df_bad["situation"].apply(lambda x: "I " + " ".join(DatasetHandler.__lemmatize(x.split(" "))))

        df_bad.drop_duplicates(subset=['rot-moral-foundations','situation_lemmatized'], inplace = True)
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("I be","I am")
        df_bad["situation_lemmatized"] = df_bad["situation_lemmatized"].str.replace("I not","I don't")
        StorageHandler.save_data_csv(df_bad, name="df_bad")

        df_bad_out = pd.DataFrame()
        df_bad_out['text'] = df_bad['situation_lemmatized']
        df_bad_out['label'] = df_bad['haidt-value']
        
        print("it's bad [unique]: ", len(df_bad["situation_lemmatized"].unique()))

        StorageHandler.save_data_csv(df_bad_out, name="df_bad_value_net")
