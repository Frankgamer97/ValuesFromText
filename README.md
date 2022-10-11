<h1>Values From Text</h1>


This project extract the text corpora from Social Chemistry dataset and aims to explain the moral concern’s polarity, based on the Haidt value, by analysing patterns in texts' RDFs, extended by ValueNet.<br>


First you need to install all the required libraries with the following command:<br>
```console
pip install -r requirements.txt
```

To run the proxy server you need to execute the following command: <br>
```shell
cd src
python app.py -api-owner=[FRED API] <--no-preprocessing> <--no-rdf-downloading> <--no-valuenet> <--no-analysis>
```
<ul>
  <li>-api-owner: specify the API key to access FRED</li>
  <li>--no-preprocessing: avoid preprocessing of Social Chemistry dataset by upload dataframes that are claculated in a previous running instance</li>
  <li>--no-rdf-downloading: avoid the download of RDFs (RDFs already exists) </li>
  <li>--no-valuenet: avoid the communication with ValueNet and load all the previous dataframe obtained in a previous running instance</li>
  <li>--no-analysis: avoid the analysis phase and produce directly the results</li>
</ul>

Note: ValueNet need to be installed locally on a Web Server. For this project it has been placed on a Fuseki web-server
