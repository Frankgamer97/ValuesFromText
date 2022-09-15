from msilib import text
from time import sleep
from zlib import adler32

import os
import pickle
import pandas as pd
import requests

class StorageHandler():

    fred_headers = {
        'accept': 'text/turtle',
        'Authorization': 'Bearer ef127c72-fa55-3075-9729-7263d0ae50d2',
    }

    @staticmethod
    def __load_pickle(file_name: str, folder: str):
        file = os.path.join(folder, file_name)
        if not os.path.exists(file):
            return None
        with open(file, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def __save_pickle(obj, file_name: str, folder: str):
        file = os.path.join(folder, file_name)

        with open(file, "wb") as f:
            pickle.dump(obj, f)

    @staticmethod
    def __save_csv(obj, columns,file_name: str, folder: str, index = False):
        file = os.path.join(folder, file_name)
        obj.to_csv(file+".csv", columns=columns, index = index )

    @staticmethod
    def __cd_parent(file):
        return os.path.dirname(file)

    @staticmethod
    def __get_project_directory():
        return StorageHandler.__cd_parent(os.path.realpath(__file__))

    @staticmethod
    def get_tmp_dir():
        return os.path.join(StorageHandler.__get_project_directory(), "tmp")

    @staticmethod
    def get_data_raw_dir():
        return os.path.join(StorageHandler.__get_project_directory(), "data", "raw")

    @staticmethod
    def get_data_preprocessed():
        return os.path.join(StorageHandler.__get_project_directory(), "data", "preprocessed")

    @staticmethod
    def get_data_rdf():
        return os.path.join(StorageHandler.__get_project_directory(), "data", "rdf")

    @staticmethod
    def create_directories():
        if not os.path.exists(StorageHandler.get_tmp_dir()):
            os.mkdir(StorageHandler.get_tmp_dir())

        if not os.path.exists(StorageHandler.get_data_raw_dir()):
            os.makedirs(StorageHandler.get_data_raw_dir())

        if not os.path.exists(StorageHandler.get_data_preprocessed()):
            os.makedirs(StorageHandler.get_data_preprocessed())

        if not os.path.exists(StorageHandler.get_data_rdf()):
            os.makedirs(StorageHandler.get_data_rdf())

    @staticmethod
    def save_data_csv(csv_table, col=None,name="csv_name", index = False):
        StorageHandler.__save_csv(csv_table, col,name, StorageHandler.get_data_preprocessed(), index = index)

    @staticmethod
    def load_csv_to_dataframe(file_path: str, sep ="\t"):
        return pd.read_csv(file_path, sep = sep)

    @staticmethod 
    def get_rdf_path(filename):
        return os.path.join( StorageHandler.get_data_rdf(), filename + ".ttl")

    @staticmethod
    def download_txt_rdf(txt, out_name):
        # file_path = os.path.join( StorageHandler.get_data_rdf(), out_name + ".ttl")
        file_path = StorageHandler.get_rdf_path(out_name)
        

        if not os.path.exists(file_path): 
            params = (
                ('text', txt), #cv),
                ('wfd_profile', 'b'),
                ('textannotation', 'earmark'),
                ('wfd', True),
                ('roles', False),
                ('alignToFramester', True),
                ('semantic-subgraph', True)
            )
            response = requests.get('http://wit.istc.cnr.it/stlab-tools/fred', headers=StorageHandler.fred_headers, params=params)

            with open(file_path,'w', encoding="utf-8") as out1: 
                out1.write(response.text)

            print(f"\tDownloaded")
            sleep(15)
        else:
            print(f"\tAlready exists")

    @staticmethod
    def get_text_hash(text):
        return str(adler32(text.encode("utf_8")))

    @staticmethod
    def retrieve_text(texts):
        for i in range(len(texts)):
            print(f"Download-{i} turtle for: {texts[i]}")

            # text_hash = str(adler32(texts[i].encode("utf_8")))
            text_hash = StorageHandler.get_text_hash(texts[i])
            StorageHandler.download_txt_rdf(texts[i], text_hash)
            