from argparse import ArgumentParser
from email.policy import default

from StorageHandler import StorageHandler
from DatasetHandler import DatasetHandler

import nltk
import os

def buildParser():
    parser=ArgumentParser()
    parser.add_argument("-api_owner",dest="api_owner", type=str, default=StorageHandler.default_api_owner)
    # parser.add_argument("--preprocess",dest="preprocess", type=str, default="True")
    # parser.add_argument("-rdf_download",dest="rdf_download", type=str, default="True")


    parser.add_argument('--rdf_downloading', default=True, action='store_true')
    parser.add_argument('--no-rdf_downloading', dest='rdf_downloading', action='store_false')

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
    owners = list(StorageHandler.fred_headers.keys())

    if args.api_owner not in owners:
        print("[WARNING] Wrong Api onwer, selecting default Api.")
        params["api_owner"] = args.api_owner

    params["api_owner"] = args.api_owner
    params["preprocessing"] = args.preprocessing
    params["rdf_downloading"] = args.rdf_downloading
    params["valuenet"] = args.valuenet
    params["analysis"] = args.analysis

    return params

if __name__ == "__main__" :
        
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

    StorageHandler.create_directories()
    DatasetHandler.download_social_chemstry()

    params = get_params()

    # for key, value in params.items():
    #     print(f"{key} => {value} (type = {type(value)})")
    
    print()
    df_fred, df_ValueNet = DatasetHandler.preprocessing(overwrite=params["preprocessing"])
    print()
    DatasetHandler.retrieve_fred_rdf(df_fred, params["api_owner"], download=params["rdf_downloading"])
    print()
    df_ValueNet = DatasetHandler.retrieve_ValueNet_data(df_fred, df_ValueNet, overwrite=params["valuenet"])
    print()
    df_ValueNet = DatasetHandler.rdf_analysis(df_ValueNet, overwrite=params["analysis"])
    print()