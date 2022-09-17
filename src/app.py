from argparse import ArgumentParser
from email.policy import default

from StorageHandler import StorageHandler
from DatasetHandler import DatasetHandler

def buildParser():
    parser=ArgumentParser()
    parser.add_argument("-api_owner",dest="api_owner", type=str, default=StorageHandler.default_api_owner)
    # parser.add_argument("--preprocess",dest="preprocess", type=str, default="True")
    # parser.add_argument("-rdf_download",dest="rdf_download", type=str, default="True")


    parser.add_argument('--rdf_downloading', default=True, action='store_true')
    parser.add_argument('--no-rdf_downloading', dest='rdf_downloading', action='store_false')

    parser.add_argument('--preprocessing', default=True, action='store_true')
    parser.add_argument('--no-preprocessing', dest='preprocessing', action='store_false')

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
        return StorageHandler.default_api_owner

    params["api_owner"] = args.api_owner
    params["preprocessing"] = args.preprocessing
    params["rdf_downloading"] = args.rdf_downloading
    params["analysis"] = args.analysis

    return params

if __name__ == "__main__" :
        
    StorageHandler.create_directories()
    DatasetHandler.download_social_chemstry()

    params = get_params()

    # for key, value in params.items():
    #     print(f"{key} => {value} (type = {type(value)})")
    print()
    df_fred, df_ValueNet = DatasetHandler.preprocessing(overwrite=params["preprocessing"])
    print()
    DatasetHandler.retrieve_fred_rdf(df_fred, params["api_owner"], download=params["rdf_downloading"])
    # print()
    # DatasetHandler.rdf_analysis(df_fred, df_ValueNet, overwrite=params["analysis"])

    print()