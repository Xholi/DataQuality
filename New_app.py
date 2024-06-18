import streamlit as st
import pandas as pd
import re
import numbers
from datetime import datetime
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Function definitions
def validate_column_type(df, column_name, expected_type):
    return df[column_name].map(lambda x: isinstance(x, expected_type))

def validate_column_regex(df, column_name, regex):
    pattern = re.compile(regex)
    return df[column_name].map(lambda x: bool(pattern.match(str(x))))

def validate_column_values_in_set(df, column_name, valid_set):
    return df[column_name].isin(valid_set)

def calculate_total_validation_percentage(validation_results):
    total_checks = len(validation_results)
    total_passed = sum(result.all() for result in validation_results.values())
    return (total_passed / total_checks) * 100

def calculate_duplication_percentage(df, column_name):
    duplicate_count = df.duplicated(subset=[column_name]).sum()
    total_count = len(df)
    return (duplicate_count / total_count) * 100

def calculate_completeness(data):
    complete_entries = 0
    for index, row in data.iterrows():
        property_value = row['PROPERTY_VALUE']
        property_uom = row['PROPERTY_UOM']
        data_type_rules = row['DATA_TYPE']
        
        if pd.api.types.is_numeric_dtype(property_value) and pd.notnull(property_uom) and data_type_rules == 'NUMERIC':
            complete_entries += 1
        elif pd.api.types.is_string_dtype(property_value) and pd.isnull(property_uom) and data_type_rules == 'STRING':
            complete_entries += 1
    
    completeness = (complete_entries / len(data)) * 100 if len(data) > 0 else 0
    return completeness

# Function to send email with attachment
def send_email(to_email, subject, body, attachment_path):
    from_email = "MantshXS@eskom.co.za"  # Replace with your email
    from_password = "fancy=Koala1918"  # Replace with your email password

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    attachment = open(attachment_path, "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= " + attachment_path)

    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

# Streamlit App
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ['Changes', 'Creations'])

if page == 'Changes':
    st.title("Changes")
else:
    st.title("Creations")

# Sidebar for file upload or SQL connection
st.sidebar.title("Upload Data")
data_source = st.sidebar.radio("Choose Data Source", ('Upload CSV', 'SQL Database'))

@st.cache_data
def load_csv(file):
    return pd.read_csv(file)

@st.cache_data
def load_sql(server, database, username, password, query):
    import pyodbc
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    return pd.read_sql(query, conn)

if data_source == 'Upload CSV':
    file_upload = st.sidebar.file_uploader("Choose a CSV file", type="csv")
    if file_upload is not None:
        df = load_csv(file_upload)
        required_columns = [
            'REQ_NO', 'REQ_TYPE', 'CORP_NO', 'ERP_NUMBER', 'DESCRIPTOR', 'PART_NUMBER', 
            'PROPERTY_TERM', 'PROPERTY_VALUE', 'PROPERTY_UOM', 'PROP_FFT', 'DATA_TYPE', 
            'STATE', 'ORIGINATOR', 'BU_CDE', 'ORG_PLANT_CODE', 'ORG_PLANT_NAME', 'CREATE_DATE', 
            'UPDATED_BY', 'UPDATED_AT', 'ATTACHMENT', 'SHORT_FORMAT_DESCRIPTION', 'MATERIAL_TYPE', 
            'MATERIAL_GROUP', 'REVISION', 'USER_DETAIL', 'USER_PROFILE', 'DIVISION', 'PLANT', 
            'REQUEST_PLANT', 'REQUEST_DIVISION', 'MONTH', 'TASK_DURATION', 'SLA_DURATION', 
            'PURCHASE_ORDER_DESCRIPTION', 'ORIGINATING_DIVISION', 'PLANT_NAME', 'PLANT_GROUP', 
            'CATALOGUING_LEVEL'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.sidebar.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.stop()
    else:
        st.sidebar.warning("Please upload a CSV file to proceed.")
        st.stop()
else:
    server = st.sidebar.text_input("SQL Server")
    database = st.sidebar.text_input("Database")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    query = st.sidebar.text_area("SQL Query")
    if st.sidebar.button("Fetch Data"):
        try:
            df = load_sql(server, database, username, password, query)
            required_columns = [
                'REQ_NO', 'REQ_TYPE', 'CORP_NO', 'ERP_NUMBER', 'DESCRIPTOR', 'PART_NUMBER', 
                'PROPERTY_TERM', 'PROPERTY_VALUE', 'PROPERTY_UOM', 'PROP_FFT', 'DATA_TYPE', 
                'STATE', 'ORIGINATOR', 'BU_CDE', 'ORG_PLANT_CODE', 'ORG_PLANT_NAME', 'CREATE_DATE', 
                'UPDATED_BY', 'UPDATED_AT', 'ATTACHMENT', 'SHORT_FORMAT_DESCRIPTION', 'MATERIAL_TYPE', 
                'MATERIAL_GROUP', 'REVISION', 'USER_DETAIL', 'USER_PROFILE', 'DIVISION', 'PLANT', 
                'REQUEST_PLANT', 'REQUEST_DIVISION', 'MONTH', 'TASK_DURATION', 'SLA_DURATION', 
                'PURCHASE_ORDER_DESCRIPTION', 'ORIGINATING_DIVISION', 'PLANT_NAME', 'PLANT_GROUP', 
                'CATALOGUING_LEVEL'
            ]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.sidebar.error(f"Missing required columns: {', '.join(missing_columns)}")
                st.stop()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
            st.stop()

# Perform validations and calculate stats
validation_checks = {
    "CORP_NO_type_check": (validate_column_type, 'CORP_NO', int),
    "ERP_NO_type_check": (validate_column_type, 'ERP_NUMBER', int),
    "DESCRIPTOR_type_check": (validate_column_type, 'DESCRIPTOR', str),
    "PROPERTY_TERM_type_check": (validate_column_type, 'PROPERTY_TERM', str),
    "PROPERTY_VALUE_check": (lambda df, column, regex: df[column].apply(lambda x: isinstance(x, numbers.Number) or isinstance(x, str)), 'PROPERTY_VALUE', None),
    "PROP_FFT_check": (validate_column_regex, 'PROP_FFT', '^[a-zA-Z\\s]*$|^NULL$'),
    "PROPERTY_UOM_type_check": (validate_column_type, 'PROPERTY_UOM', str),
    "DATA_TYPE_type_check": (validate_column_type, 'DATA_TYPE', str),
    "STATE_type_check": (validate_column_type, 'STATE', str),
    "ORIGINATOR_type_check": (validate_column_type, 'ORIGINATOR', str),
    "BU_CDE_type_check": (validate_column_type, 'BU_CDE', str),
    "ORG_PLANT_CODE_type_check": (validate_column_type, 'ORG_PLANT_CODE', str),
    "ORG_PLANT_NAME_type_check": (validate_column_type, 'ORG_PLANT_NAME', str),
    "CREATE_DATE_type_check": (validate_column_type, 'CREATE_DATE', str),
    "UPDATED_BY_type_check": (validate_column_type, 'UPDATED_BY', str),
    "UPDATED_AT_type_check": (validate_column_type, 'UPDATED_AT', str),
    "ATTACHMENT_type_check": (validate_column_type, 'ATTACHMENT', str),
    "SHORT_FORMAT_DESCRIPTION_type_check": (validate_column_type, 'SHORT_FORMAT_DESCRIPTION', str),
    "MATERIAL_TYPE_type_check": (validate_column_type, 'MATERIAL_TYPE', str),
    "MATERIAL_GROUP_type_check": (validate_column_type, 'MATERIAL_GROUP', str),
    "REVISION_type_check": (validate_column_type, 'REVISION', str),
    "USER_DETAIL_type_check": (validate_column_type, 'USER_DETAIL', str),
    "USER_PROFILE_type_check": (validate_column_type, 'USER_PROFILE', str),
    "DIVISION_type_check": (validate_column_type, 'DIVISION', str),
    "PLANT_type_check": (validate_column_type, 'PLANT', str),
    "REQUEST_PLANT_type_check": (validate_column_type, 'REQUEST_PLANT', str),
    "REQUEST_DIVISION_type_check": (validate_column_type, 'REQUEST_DIVISION', str),
    "MONTH_type_check": (validate_column_type, 'MONTH', str),
    "TASK_DURATION_type_check": (validate_column_type, 'TASK_DURATION', str),
    "SLA_DURATION_type_check": (validate_column_type, 'SLA_DURATION', str),
    "PURCHASE_ORDER_DESCRIPTION_type_check": (validate_column_type, 'PURCHASE_ORDER_DESCRIPTION', str),
    "ORIGINATING_DIVISION_type_check": (validate_column_type, 'ORIGINATING_DIVISION', str),
    "PLANT_NAME_type_check": (validate_column_type, 'PLANT_NAME', str),
    "PLANT_GROUP_type_check": (validate_column_type, 'PLANT_GROUP', str),
    "CATALOGUING_LEVEL_type_check": (validate_column_type, 'CATALOGUING_LEVEL', str)
}

validation_results = {}
for check_name, (check_func, column, param) in validation_checks.items():
    if param is not None:
        validation_results[check_name] = check_func(df, column, param)
    else:
        validation_results[check_name] = check_func(df, column)

total_validation_percentage = calculate_total_validation_percentage(validation_results)
duplication_percentage = calculate_duplication_percentage(df, 'ERP_NUMBER')
completeness_percentage = calculate_completeness(df)

st.write("### Data Quality Report")
st.write(f"**Total Validation Percentage:** {total_validation_percentage:.2f}%")
st.write(f"**Duplication Percentage:** {duplication_percentage:.2f}%")
st.write(f"**Completeness Percentage:** {completeness_percentage:.2f}%")

# Email functionality
st.sidebar.title("Send Report via Email")
recipient_email = st.sidebar.text_input("Recipient Email")
subject = st.sidebar.text_input("Email Subject")
body = st.sidebar.text_area("Email Body")
if st.sidebar.button("Send Email"):
    if recipient_email and subject and body:
        report_path = "data_quality_report.csv"
        df.to_csv(report_path, index=False)
        send_email(recipient_email, subject, body, report_path)
        st.sidebar.success("Email sent successfully!")
    else:
        st.sidebar.error("Please fill all the email fields.")
