# Import

REDCap API Documentation
Method Name
Import Records

Description
This method allows you to import a set of records for a project

URL
https://rc.health.unm.edu/manage/api/
Supported Request Method
POST
Permissions Required
To use this method, you must have API Import/Update privileges in the project.
Parameters (case sensitive)
Required
token
The API token specific to your REDCap project and username (each token is unique to each user for each project). See the section on the left-hand menu for obtaining a token for a given project.
content
record
format
csv, json, xml [default], odm ('odm' refers to CDISC ODM XML format, specifically ODM version 1.3.1)
type
flat - output as one record per row [default]
eav - input as one data point per row
Non-longitudinal: Will have the fields - record*, field_name, value
Longitudinal: Will have the fields - record*, field_name, value, redcap_event_name
* 'record' refers to the record ID for the project
** Event name is the unique name for an event, not the event label
overwriteBehavior
normal - blank/empty values will be ignored [default]
overwrite - blank/empty values are valid and will overwrite data
forceAutoNumber
If record auto-numbering has been enabled in the project, it may be desirable to import records where each record's record name is automatically determined by REDCap (just as it does in the user interface). If this parameter is set to 'true', the record names provided in the request will not be used (although they are still required in order to associate multiple rows of data to an individual record in the request), but instead those records in the request will receive new record names during the import process. NOTE: To see how the provided record names get translated into new auto record names, the returnContent parameter should be set to 'auto_ids', which will return a record list similar to 'ids' value, but it will have the new record name followed by the provided record name in the request, in which the two are comma-delimited. For example, if
false (or 'false') - The record names provided in the request will be used. [default]
true (or 'true') - New record names will be automatically determined.
backgroundProcess
Specifies whether to do the import as background process.
0 or 'false' for no. [default]
1 or 'true' for yes.
data
The formatted data to be imported.

TIP: If importing repeating instances for a repeating event or repeating instrument, you may auto-number the instances by providing a value of 'new' for the 'redcap_repeat_instance' field in the dataset you are importing. This is useful because it allows you to import such data without the need to determine how many instances already exist for a given repeating event/instance prior to the import. NOTICE: The 'new' value option for auto-numbering instances does NOT work for 'eav' type data but only for 'flat' type.

NOTE: When importing data in EAV type format, please be aware that checkbox fields must have their field_name listed as variable+'___'+optionCode and its value as either '0' or '1' (unchecked or checked, respectively). For example, for a checkbox field with variable name 'icecream', it would be imported as EAV with the field_name as 'icecream___4' having a value of '1' in order to set the option coded with '4' (which might be 'Chocolate') as 'checked'.
EAV XML:

<?xml version="1.0" encoding="UTF-8" ?>
<records>
   <item>
      <record></record>
      <field_name></field_name>
      <value></value>
      <redcap_event_name></redcap_event_name>
   </item>
</records>
Flat XML:

<?xml version="1.0" encoding="UTF-8" ?>
<records>
   <item>
      each data point as an element
      ...
   </item>
</records>
Optional
dateFormat
MDY, DMY, YMD [default] - the format of values being imported for dates or datetime fields (understood with M representing 'month', D as 'day', and Y as 'year') - NOTE: The default format is Y-M-D (with dashes), while MDY and DMY values should always be formatted as M/D/Y or D/M/Y (with slashes), respectively.
csvDelimiter
Set the delimiter used to separate values in the CSV data file (for CSV format only). Options include: comma ',' (default), 'tab', semi-colon ';', pipe '|', or caret '^'. Simply provide the value in quotes for this parameter.
returnContent
count [default] - the number of records imported, ids - a list of all record IDs that were imported, auto_ids = (used only when forceAutoNumber=true) a list of pairs of all record IDs that were imported, includes the new ID created and the ID value that was sent in the API request (e.g., 323,10).
NOTE: Does not apply when importing as a background process (i.e., backgroundProcess=true). When using a background process, success:true (upon success) or success:false (upon failure) will be returned in the appropriate format (csv, json, xml).
returnFormat
csv, json, xml - specifies the format of error messages. If you do not pass in this flag, it will select the default format for you passed based on the 'format' flag you passed in or if no format flag was passed in, it will default to 'xml'.
NOTE: Does not apply when importing as a background process (i.e., backgroundProcess=true). When using a background process, success:true (upon success) or success:false (upon failure) will be returned in the appropriate format (csv, json, xml).
Returns
the content specified by returnContent

# Export

REDCap API Documentation
Method Name
Export Records

Description
This method allows you to export a set of records for a project.

Note about export rights: Please be aware that Data Export user rights will be applied to this API request. For example, if you have 'No Access' data export rights in the project, then the API data export will fail and return an error. And if you have 'De-Identified' or 'Remove All Identifier Fields' data export rights, then some data fields *might* be removed and filtered out of the data set returned from the API. To make sure that no data is unnecessarily filtered out of your API request, you should have 'Full Data Set' export rights in the project.

URL
https://rc.health.unm.edu/manage/api/
Supported Request Method
POST
Permissions Required
To use this method, you must have API Export privileges in the project.
Parameters (case sensitive)
Required
token
The API token specific to your REDCap project and username (each token is unique to each user for each project). See the section on the left-hand menu for obtaining a token for a given project.
content
record
format
csv, json, xml [default], odm ('odm' refers to CDISC ODM XML format, specifically ODM version 1.3.1)
type
flat - output as one record per row [default]
eav - output as one data point per row
Non-longitudinal: Will have the fields - record*, field_name, value
Longitudinal: Will have the fields - record*, field_name, value, redcap_event_name
* 'record' refers to the record ID for the project
Optional
records
an array of record names specifying specific records you wish to pull (by default, all records are pulled)
fields
an array of field names specifying specific fields you wish to pull (by default, all fields are pulled) or alternatively as a string (comma-separated list).
forms
an array of form names you wish to pull records for. If the form name has a space in it, replace the space with an underscore (by default, all records are pulled)
events
an array of unique event names that you wish to pull records for - only for longitudinal projects
rawOrLabel
raw [default], label - export the raw coded values or labels for the options of multiple choice fields
rawOrLabelHeaders
raw [default], label - (for 'csv' format 'flat' type only) for the CSV headers, export the variable/field names (raw) or the field labels (label)
exportCheckboxLabel
true, false [default] - specifies the format of checkbox field values specifically when exporting the data as labels (i.e., when rawOrLabel=label) in flat format (i.e., when type=flat). When exporting labels, by default (without providing the exportCheckboxLabel flag or if exportCheckboxLabel=false), all checkboxes will either have a value 'Checked' if they are checked or 'Unchecked' if not checked. But if exportCheckboxLabel is set to true, it will instead export the checkbox value as the checkbox option's label (e.g., 'Choice 1') if checked or it will be blank/empty (no value) if not checked. If rawOrLabel=false or if type=eav, then the exportCheckboxLabel flag is ignored. (The exportCheckboxLabel parameter is ignored for type=eav because 'eav' type always exports checkboxes differently anyway, in which checkboxes are exported with their true variable name (whereas the 'flat' type exports them as variable___code format), and another difference is that 'eav' type *always* exports checkbox values as the choice label for labels export, or as 0 or 1 (if unchecked or checked, respectively) for raw export.)
returnFormat
csv, json, xml - specifies the format of error messages. If you do not pass in this flag, it will select the default format for you passed based on the 'format' flag you passed in or if no format flag was passed in, it will default to 'xml'.
exportSurveyFields
true, false [default] - specifies whether or not to export the survey identifier field (e.g., 'redcap_survey_identifier') or survey timestamp fields (e.g., instrument+'_timestamp') when surveys are utilized in the project. If you do not pass in this flag, it will default to 'false'. If set to 'true', it will return the redcap_survey_identifier field and also the survey timestamp field for a particular survey when at least one field from that survey is being exported. NOTE: If the survey identifier field or survey timestamp fields are imported via API data import, they will simply be ignored since they are not real fields in the project but rather are pseudo-fields.
exportDataAccessGroups
true, false [default] - specifies whether or not to export the 'redcap_data_access_group' field when data access groups are utilized in the project. If you do not pass in this flag, it will default to 'false'. NOTE: This flag is only viable if the user whose token is being used to make the API request is *not* in a data access group. If the user is in a group, then this flag will revert to its default value.
filterLogic
String of logic text (e.g., [age] > 30) for filtering the data to be returned by this API method, in which the API will only return the records (or record-events, if a longitudinal project) where the logic evaluates as TRUE. This parameter is blank/null by default unless a value is supplied. Please note that if the filter logic contains any incorrect syntax, the API will respond with an error message.
dateRangeBegin
To return only records that have been created or modified *after* a given date/time, provide a timestamp in the format YYYY-MM-DD HH:MM:SS (e.g., '2017-01-01 00:00:00' for January 1, 2017 at midnight server time). If not specified, it will assume no begin time.
dateRangeEnd
To return only records that have been created or modified *before* a given date/time, provide a timestamp in the format YYYY-MM-DD HH:MM:SS (e.g., '2017-01-01 00:00:00' for January 1, 2017 at midnight server time). If not specified, it will use the current server time.
csvDelimiter
Set the delimiter used to separate values in the CSV data file (for CSV format only). Options include: comma ',' (default), 'tab', semi-colon ';', pipe '|', or caret '^'. Simply provide the value in quotes for this parameter.
decimalCharacter
If specified, force all numbers into same decimal format. You may choose to force all data values containing a decimal to have the same decimal character, which will be applied to all calc fields and number-validated text fields. Options include comma ',' or dot/full stop '.', but if left blank/null, then it will export numbers using the fields' native decimal format. Simply provide the value of either ',' or '.' for this parameter.
exportBlankForGrayFormStatus
true, false [default] - specifies whether or not to export blank values for instrument complete status fields that have a gray status icon. All instrument complete status fields having a gray icon can be exported either as a blank value or as "0" (Incomplete). Blank values are recommended in a data export if the data will be re-imported into a REDCap project.
Returns
Data from the project in the format and type specified ordered by the record (primary key of project) and then by event id

EAV XML:

<?xml version="1.0" encoding="UTF-8" ?>
<records>
   <item>
      <record></record>
      <field_name></field_name>
      <value></value>
      <redcap_event_name></redcap_event_name>
   </item>
</records>
Flat XML:

<?xml version="1.0" encoding="UTF-8" ?>
<records>
   <item>
      each data point as an element
      ...
   </item>
</records>