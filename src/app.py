from argparse import ArgumentParser
from email.policy import default

from StorageHandler import StorageHandler
from DatasetHandler import DatasetHandler

import nltk
import os

def buildParser():
    parser=ArgumentParser()
    parser.add_argument("-fred-api-file",dest="fred_api_file", type=str, default="")
    parser.add_argument("-api-owner",dest="api_owner", type=str, default="")
    # parser.add_argument("--preprocess",dest="preprocess", type=str, default="True")
    # parser.add_argument("-rdf_download",dest="rdf_download", type=str, default="True")


    parser.add_argument('--rdf-downloading', default=True, action='store_true')
    parser.add_argument('--no-rdf-downloading', dest='rdf_downloading', action='store_false')

    parser.add_argument('--preprocessing', default=True, action='store_true')
    parser.add_argument('--no-preprocessing', dest='preprocessing', action='store_false')

    parser.add_argument('--valuenet', default=True, action='store_true')
    parser.add_argument('--no-valuenet', dest='valuenet', action='store_false')

    parser.add_argument('--analysis', default=True, action='store_true')
    parser.add_argument('--no-analysis', dest='analysis', action='store_false')

    return parser

def get_params():
    parser = buildParser()
    args = parser.parse_args()

    params = {}
    params["api_owner"] = args.api_owner

    params["api-owner"] = args.api_owner
    params["preprocessing"] = args.preprocessing
    params["rdf-downloading"] = args.rdf_downloading
    params["valuenet"] = args.valuenet
    params["analysis"] = args.analysis
    params["fred_api_file"] = args.fred_api_file

    return params

if __name__ == "__main__" :
    
    params = get_params()
    if params["rdf-downloading"]:
        if params["fred_api_file"] == "":
            params["fred_api_file"] = "FRED_API.txt"
            print("[WARNING] No FRED API key file selected, using the default file if exist")

        assert StorageHandler.load_api(params["fred_api_file"])

        owners = list(StorageHandler.fred_headers.keys())
        if params["api_owner"] not in owners:
            print("[WARNING] No valid FRED Api owner, selecting default Api.")
    

    apt = False
    wn = False
    omv = False

    try:
        nltk.data.find(os.path.join('taggers','averaged_perceptron_tagger'))
        apt = True
        nltk.data.find(os.path.join('corpora','wordnet'))
        wn = True
        nltk.data.find(os.path.join('corpora','omw-1.4'))
        omv = True
    except:
        if not apt:
            nltk.download('averaged_perceptron_tagger')
        if not wn:
            nltk.download('wordnet')
        if not omv:
            nltk.download('omw-1.4')



    print()

    StorageHandler.create_directories()
    DatasetHandler.download_social_chemstry()
    StorageHandler.Glove()
    
    print()
    df_fred, df_ValueNet, dyads_dict= DatasetHandler.preprocessing(overwrite=params["preprocessing"])

    print()
    DatasetHandler.retrieve_fred_rdf(df_ValueNet, params["api-owner"], download=params["rdf-downloading"])
    print()
    df_ValueNet, is_ok = DatasetHandler.retrieve_ValueNet_data(df_ValueNet, overwrite=params["valuenet"])

    # df_ValueNet["text_hash"] = df_ValueNet["text"].apply(lambda x: StorageHandler.get_text_hash(x))
    # columns = list(df_ValueNet.columns)
    # df_ValueNet = df_ValueNet[[columns[0]] + ["text_hash"] + columns[1:]]
    # StorageHandler.save_data_csv(df_ValueNet, name="df_ValueNet_response")
    
    if is_ok:
        print()
        df_ValueNet = DatasetHandler.rdf_statistical_analysis(df_ValueNet, dyads_dict, overwrite=params["analysis"])
        print()
        df_ValueNet = DatasetHandler.rdf_semantic_analysis(df_ValueNet, overwrite=params["analysis"])
        print()