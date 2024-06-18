
Data Quality Dashboard App
This Streamlit app allows users to upload a CSV file or connect to an SQL database to perform data quality checks. It validates data against predefined rules, calculates duplication and completeness percentages, and visualizes the results. Additionally, users can send the data quality report via email.

Features
Upload data from a CSV file or an SQL database
Validate data against predefined rules
Calculate total validation, duplication, and completeness percentages
Visualize data quality metrics using bar charts
Send data quality reports via email
Getting Started
Prerequisites
Python 3.7 or later
Streamlit
pandas
plotly
smtplib
email
pyodbc (for SQL database connections)
Installation
Clone the repository:

bash
Copy code
git clone https://github.com/your-repo/data-quality-dashboard.git
cd data-quality-dashboard
Install the required Python packages:

bash
Copy code
pip install -r requirements.txt
Run the Streamlit app:

bash
Copy code
streamlit run app.py
Usage
Navigation
Use the sidebar to navigate between the "Changes" and "Creations" pages.

Upload Data
Upload CSV:

Choose "Upload CSV" from the sidebar.
Upload a CSV file containing the data.
SQL Database:

Choose "SQL Database" from the sidebar.
Enter the SQL server, database, username, password, and query details.
Click "Fetch Data" to load the data from the database.
Data Quality Checks
The app performs the following checks:

Validation Checks: Ensures data types and formats are correct.
Duplication Checks: Calculates the percentage of duplicate records.
Completeness Checks: Calculates the percentage of complete records based on predefined rules.
Visualization
The results are visualized using a bar chart showing:

Total validation percentage
Duplication percentage
Completeness percentage
Send Report via Email
Enter the recipient's email address, subject, and body of the email in the sidebar.
Click "Send Email" to send the data quality report as a CSV attachment.
Validation Rules
The following columns are required for the data quality checks:

REQ_NO
REQ_TYPE
CORP_NO
ERP_NUMBER
DESCRIPTOR
PART_NUMBER
PROPERTY_TERM
PROPERTY_VALUE
PROPERTY_UOM
PROP_FFT
DATA_TYPE
STATE
ORIGINATOR
BU_CDE
ORG_PLANT_CODE
ORG_PLANT_NAME
CREATE_DATE
UPDATED_BY
UPDATED_AT
ATTACHMENT
SHORT_FORMAT_DESCRIPTION
MATERIAL_TYPE
MATERIAL_GROUP
REVISION
USER_DETAIL
USER_PROFILE
DIVISION
PLANT
REQUEST_PLANT
REQUEST_DIVISION
MONTH
TASK_DURATION
SLA_DURATION
PURCHASE_ORDER_DESCRIPTION
ORIGINATING_DIVISION
PLANT_NAME
PLANT_GROUP
CATALOGUING_LEVEL
Each column is validated for its data type and format, ensuring the data is clean and consistent.

Contact
For any questions or issues, please contact Xholi.mantshongo@gmail.com
