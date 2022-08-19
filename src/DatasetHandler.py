from StorageHandler import StorageHandler
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