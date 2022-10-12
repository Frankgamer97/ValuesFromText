<h1>Values From Text</h1>


This project extract the text corpora from Social Chemistry dataset and aims to explain the moral concern’s polarity, based on the Haidt value, by analysing patterns in texts' RDFs, extended by ValueNet.<br>


First you need to install all the required libraries with the following command:<br>
```console
pip install -r requirements.txt
```

To run the proxy server you need to execute the following command: <br>
```shell
cd src
python app.py <-fred-api-file=[FRED FILE]> <-api-owner=[OWNER OF THE KEY]> <--no-preprocessing> <--no-rdf-downloading> <--no-valuenet> <--no-analysis>
```
<ul>
  <li><b>-fred-api-file</b>: specify the API key file to access FRED. If not specified the script will try to open the default file "FRED_API.txt". The file must be built as a sequence of "<api_owner> <key>". It also must be contained in the root directory.</li>

  <li><b>-api_owner</b>: specify the API key owner to access FRED. If the FRED Api key file contains more than one key, the amount of RDFs required to FRED is distributed to the different keys. If the FRED Api file contains only one key, this params is not mandatory but the full amount of RDFs will be downloaded by that single key. If the api owner isn't specified, the first api key is selected.</li>

  <li><b>--no-preprocessing</b>: avoid preprocessing of Social Chemistry dataset by upload dataframes that are claculated in a previous running instance</li>
  <li><b>--no-rdf-downloading</b>: avoid the download of RDFs (RDFs already exists) </li>
  <li><b>--no-valuenet</b>: avoid the communication with ValueNet and load all the previous dataframe obtained in a previous running instance</li>
  <li><b>--no-analysis</b>: avoid the analysis phase and produce directly the results</li>
</ul>

Note: ValueNet need to be installed locally on a Web Server. For this project it has been placed on a Fuseki web-server.
