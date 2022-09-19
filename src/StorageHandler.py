from time import sleep
from zlib import adler32

import os
import pickle
import pandas as pd
import requests
import rdflib
import json

class StorageHandler():


    default_api_owner = "Francesco"
    fred_headers = {
        "Francesco": {
            'accept': 'text/turtle',
            'Authorization': 'Bearer ef127c72-fa55-3075-9729-7263d0ae50d2',
        },
        "Primiano": {
            'accept': 'text/turtle',
            'Authorization': 'Bearer e7c13f41-a79e-367f-9a47-d532fce077c0',
        }# ,
        # "Luciano": {
        #     'accept': 'text/turtle',
        #     'Authorization': 'Bearer 16a84b70-1b8d-3d05-8d1a-7a37da9be9e8',
        # }
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
    def get_data_rdf_extended():
        return os.path.join(StorageHandler.__get_project_directory(), "data", "rdf_extended")

    def get_propreccesed_file_path(filename):
        return os.path.join(StorageHandler.__get_project_directory(), "data", "preprocessed", filename)

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

        if not os.path.exists(StorageHandler.get_data_rdf_extended()):
            os.makedirs(StorageHandler.get_data_rdf_extended())



    @staticmethod
    def save_data_csv(csv_table, col=None,name="csv_name", index = False):
        StorageHandler.__save_csv(csv_table, col,name, StorageHandler.get_data_preprocessed(), index = index)

    @staticmethod
    def load_csv_to_dataframe(file_path: str, sep =","):
        try:
            return pd.read_csv(file_path, sep = sep)
        except FileNotFoundError as e:
            return None

    @staticmethod 
    def get_rdf_path(filename, extended = False):
        if extended:
            return os.path.join( StorageHandler.get_data_rdf_extended(), filename + ".ttl")
        return os.path.join( StorageHandler.get_data_rdf(), filename + ".ttl")


    @staticmethod
    def save_rdf(turtle_name, data, extended = False):
        turtle_path = StorageHandler.get_rdf_path(turtle_name, extended=extended)

        with open(turtle_path,'w', encoding="utf-8") as file: 

            if extended:
                file.write(data.serialize(format='turtle'))
            else:
                file.write(data)

    @staticmethod
    def save_json(json_name, data):
        file_path = StorageHandler.get_propreccesed_file_path(json_name)

        data_json = json.loads(json.dumps(data))
        with open(file_path, "w") as f: 
            json.dump(data_json, f, ensure_ascii=False, indent=4)
        
    @staticmethod
    def load_json(json_name):
        file_path = StorageHandler.get_propreccesed_file_path(json_name)
        with open(file_path, "r") as f:

            data_json = str(json.load(f))
        return data_json
        
    @staticmethod
    def download_txt_rdf(txt, out_name, headers):
        file_path = StorageHandler.get_rdf_path(out_name, extended=False)

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
            response = requests.get('http://wit.istc.cnr.it/stlab-tools/fred', headers=headers, params=params)

            StorageHandler.save_rdf(out_name, response.text, extended=False)

            try:
                rdflib.Graph().parse(file_path,format='ttl')
                print("\tDownloaded")
            except:
                print("\t[WARNING] Damaged")
            
            sleep(15)
        else:
            print("\tAlready exists")

    @staticmethod
    def get_text_hash(text):
        return str(adler32(text.encode("utf_8")))

    @staticmethod
    def retrieve_text(texts, api_owner):
        headers = list(StorageHandler.fred_headers.values())[0]

        owners = list(StorageHandler.fred_headers.keys())
        owners_len = len(owners)
        owner_index = owners.index(api_owner)
        owner_slot_len = int(len(texts)/owners_len)

        owner_slot_index_start = owner_index * owner_slot_len
        owner_slot_index_end = owner_slot_index_start + owner_slot_len

        if owner_index == owners_len - 1:
            owner_slot_index_end = len(texts)

        print()
        print("[DOWNLOADING TURTLE FILES]")
        print()
        
        for i in range(owner_slot_index_start, owner_slot_index_end):
            print(f"Download-{i} turtle for: {texts[i]}")

            # text_hash = str(adler32(texts[i].encode("utf_8")))
            text_hash = StorageHandler.get_text_hash(texts[i])
            StorageHandler.download_txt_rdf(texts[i], text_hash, headers)
        
        print()
        print("[DOWNLOADING TURTLE FILES COMPLETED]")
        print()
        
            