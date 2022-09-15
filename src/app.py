from argparse import ArgumentParser

from StorageHandler import StorageHandler
from DatasetHandler import DatasetHandler

def buildParser():
    parser=ArgumentParser()
    # parser.add_argument("-hashseed",dest="hashseed", type=str, default="")

    return parser

def is_hashseed_set():
    parser = buildParser()
    args = parser.parse_args()

if __name__ == "__main__" :
        
    StorageHandler.create_directories()
    DatasetHandler.download_social_chemstry()
    print()
    df_fred, df_ValueNet = DatasetHandler.preprocessing()
    print()
    DatasetHandler.rdf_analysis(df_fred, df_ValueNet)
    print()