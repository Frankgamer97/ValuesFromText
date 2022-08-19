from StorageHandler import StorageHandler
from DatasetHandler import DatasetHandler

if __name__ == "__main__" :
    StorageHandler.create_directories()
    DatasetHandler.download_social_chemstry()
    print()
    DatasetHandler.preprocessing()
    print()