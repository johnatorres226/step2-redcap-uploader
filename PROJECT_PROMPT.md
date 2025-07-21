'''
This fetcher/uploader modules will work together to perform the following tasks: 

(1) Export current data for the QC STATUS tool in ADRC UDSv4 REDCap
(2) Import QC Status data into the QC STATUS tool and ovewrwrite existing data.

Between the export and import and ovwerriting documetnaiton file will be created to capture
the changes made to the QC Status data. This changes file will contain the following:
- Previous data
- New data

This is to help as a fallback in case we need to revert the changes made by the import.

This mechanism will also be used to address any querry errors adderess by the clinical team.
The team will provide a csv or excel file with the changes to be made, and will be converted
to json file to upload. This will be in the data directory. This process will also have the
overwrite documentation file created to capture the changes made.

Starting with upload the QC Status Report Data.
The source of the data will come from json files from the Step 1 process and be located at the UPLOAD_READY_PATH.
We have to use relative paths to ensure we capture only the lastest data and check if that data has already been uploaded.
Hence, a logging mechanism will be implemented to track the changes made to the QC Status data,
and preferrably this logging mechanism will output a tracking file. 

After the upload, the meachnism will output the log files of what changes were made
and the fallback files to reveret the changes if needed.
This will be the end of the upload process for the QC Status Report Data.

The Query Resolution Upload Process.
This process will be similar to the upload process, but instead of uploading the QC Status Report Data,
we will upload the Query Resolution Data. The source of the data will come from a csv or excel file
provided by the clinical team. This file will be converted to a json file and uploaded to the
REDCap project. The same logging mechanism will be implemented to track the changes made to the Query Resolution Data,
and a tracking file will be outputted to capture the changes made. Hence, we will extracting the current data
from REDCap, and overwrite with with the new data provided. This process will be tracked and logged
in the same manner. 

The assumptions and features of this project are as follows:
- The REDCap API is used to interact with the REDCap project.
- The data source for the QC Status Report Data is a json file located at the UPLOAD_READY_PATH.
- The data source for the Query Resolution Data is a csv or excel file provided by the clinical team
    this data should be located in this project directory or it should be referenced in the env file
- The logging mechanism will output a tracking file to capture the changes made to the QC Status Report 
    Data and Query Resolution Data.

Core technical functionality:
- This should be execuatble via cli and hence a cli.py file will be created to handle the command line interface, with
    the handle name: udsv4-redcap-uploader [command] [options] with --intiials [TEXT] always being required
    such that they will be used in the LOG_FILE.txt file.
- The focus should be simplicity and efficiency, with clear and concise code.
- Output should create a subdirectoy everytime in format: REDCAP_UPLOAD_{date format: DDMMMYYYY} and it should contain:
FALLBACK_FILE_{date stamp}.json, DATA_UPLOAD_RECIPT_{date stamp}.json, and LOG_FILE.txt.
- The logging mechanism should be implemented using the logging module in Python which will serve to 
track the changes made to the QC Status Report Data and Query Resolution Data, and be visible in command line.
- There should be a comprehensive logging tracker where each interations is writes the file uploaded (from the UPLOAD_READY_PATH), the date,
    the intials, and there should be a backup file at the discrete location using BACKUP_LOG_PATH.
- The use of discriminatory variable logical processing to determine if the data has been uploaded or not. Teh variable qc_last_run
    will be used to determine if the data has been uploaded or not. If the data being uploaded has the same value as the last run,
    then the data will not be uploaded and a message will be logged indicating that the data has already been uploaded.

Testing
This project should use pytest to test the core functionality of the fetcher/uploader modules.

Conventions:
- date stamp format: DDMMMYYYY
- file names should be in uppercase for the first letter only, and use underscores for spaces
- coding conventions should follow PEP 8 guidelines

Logging
We will use a logging.py file to handle the logging mechanism. This will be used for the CLI interface. 
The logging of changes will be the data streamed via upload/fetching processes, and will be written to a log file.
The log file will be named LOG_FILE.txt and will be located in the output directory created by the upload process.
Every iterarion will also written in to a comprehensive log file which will serve as the primary tracker.
This tracker will determine inital upload for QC status data, and for the Query Resolution Data. A copy of this
log will be saved in the BACKUP_LOG_PATH directory.

Discriminatory Variable Logical Processing
The REDCap project contains the variable: qc_last_run which is also used in the json files for the QC Status Report Data.
This variable will also be used to determine if the data has been uploaded or not. If the data being uploaded has the same value
as the last run, then the data will not be uploaded and a message will be logged indicating that the data has already been uploaded.
Hence, for that record, the data will not be uploaded. This processing will be stoped for that record and the next record will be processed.

Workflow:
1. Fetch current data from REDCap project for QC Status Report Data.
2. Check if the data has already been uploaded by comparing the qc_last_run variable.
3. If the data has not been uploaded, upload the data from the UPLOAD_READY_PATH
4. Log the changes made to the QC Status Report Data and Query Resolution Data, and output a tracking file and backup file.
5. Output the log file and the fallback file to revert changes if needed.

Logging handdled by the logging.py module. cli.py will handle the command line interface.
uploader.py will handle upload. fetcher.py will handle fetching the data from REDCap.
file_monitor.py will handle monitoring the files for changes and tracking processing history.
data_processor.py will handle processing the data and converting it to the required format.
change_tracker.py will handle tracking the changes made to the data.
config.py will handle the configuration settings for the project.
pytest will be used to test the core functionality of the fetcher/uploader modules.
'''
