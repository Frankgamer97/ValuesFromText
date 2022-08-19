import os
import pickle
# import pandas as pd

class StorageHandler():

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
    def __save_csv(obj, columns,file_name: str, folder: str):
        file = os.path.join(folder, file_name)
        obj.to_csv(file+".csv", columns=columns )

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
    def create_directories():
        if not os.path.exists(StorageHandler.get_tmp_dir()):
            os.mkdir(StorageHandler.get_tmp_dir())

        if not os.path.exists(StorageHandler.get_data_raw_dir()):
            os.makedirs(StorageHandler.get_data_raw_dir())

        if not os.path.exists(StorageHandler.get_data_preprocessed()):
            os.makedirs(StorageHandler.get_data_preprocessed())

    @staticmethod
    def save_data_csv(csv_table, col=None,name="csv_name"):
        StorageHandler.__save_csv(csv_table, col,name, StorageHandler.get_data_raw_dir())