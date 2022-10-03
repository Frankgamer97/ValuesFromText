from argparse import ArgumentParser
from email.policy import default

from StorageHandler import StorageHandler
from DatasetHandler import DatasetHandler

import nltk
import os

def buildParser():
    parser=ArgumentParser()
    parser.add_argument("-api-owner",dest="api_owner", type=str, default=StorageHandler.default_api_owner)
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
    owners = list(StorageHandler.fred_headers.keys())

    if args.api_owner not in owners:
        print("[WARNING] Wrong Api onwer, selecting default Api.")
        params["api_owner"] = args.api_owner

    params["api-owner"] = args.api_owner
    params["preprocessing"] = args.preprocessing
    params["rdf-downloading"] = args.rdf_downloading
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
    StorageHandler.Glove()

    params = get_params()

    # for key, value in params.items():
    #     print(f"{key} => {value} (type = {type(value)})")
    
    print()
    df_fred, df_ValueNet= DatasetHandler.preprocessing(overwrite=params["preprocessing"])

    # texts = df_fred["text"].tolist()
    # texts_valuenet = df_ValueNet["text"].tolist()

    # print()
    # print(len(texts))
    # print(len([ el for el in texts if el in texts_valuenet]))
    # print()
    # print(len(texts_valuenet))
    # print(len([ el for el in texts_valuenet if el in texts]))
    # print()

    print()
    DatasetHandler.retrieve_fred_rdf(df_ValueNet, params["api-owner"], download=params["rdf-downloading"])
    print()
    df_ValueNet = DatasetHandler.retrieve_ValueNet_data(df_ValueNet, overwrite=params["valuenet"])
    print()
    df_ValueNet = DatasetHandler.rdf_statistical_analysis(df_ValueNet, overwrite=params["analysis"])
    print()
    df_ValueNet = DatasetHandler.rdf_semantic_analysis(df_ValueNet, overwrite=params["analysis"])
    print()