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
        data_type_rules = row['VALUE_TYPE_RULES']
        
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
            'CORP_NO', 'ERP_NUMBER', 'DESCRIPTOR_TERM', 'PROPERTY_TERM', 'PROPERTY_VALUE', 
            'POD', 'PROP_FFT', 'PROPERTY_UOM', 'UOM_RULES', 'VALUE_TYPE_RULES', 
            'DATA_TYPE', 'ORIGINATING_PLANT_TRM', 'ORIGINATING_DIVISION', 'PLANT_GROUP', 
            'MAND_IND', 'MAND_EMPTY'
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
                'CORP_NO', 'ERP_NUMBER', 'DESCRIPTOR_TERM', 'PROPERTY_TERM', 'PROPERTY_VALUE', 
                'POD', 'PROP_FFT', 'PROPERTY_UOM', 'UOM_RULES', 'VALUE_TYPE_RULES', 
                'DATA_TYPE', 'ORIGINATING_PLANT_TRM', 'ORIGINATING_DIVISION', 'PLANT_GROUP', 
                'MAND_IND', 'MAND_EMPTY'
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
    "DESCR_type_check": (validate_column_type, 'DESCRIPTOR_TERM', str),
    "PROPERTY_TERM_type_check": (validate_column_type, 'PROPERTY_TERM', str),
    "PROPERTY_VALUE_check": (lambda df, column, regex: df[column].apply(lambda x: isinstance(x, numbers.Number) or isinstance(x, str)), 'PROPERTY_VALUE', None),
    "POD_check": (validate_column_regex, 'POD', '^[a-zA-Z\\s]*$|^NULL$'),
    "PROP_FFT_check": (validate_column_regex, 'PROP_FFT', '^[a-zA-Z\\s]*$|^NULL$'),
    "PROPERTY_UOM_type_check": (validate_column_type, 'PROPERTY_UOM', str),
    "UOM_RULES_type_check": (validate_column_type, 'UOM_RULES', str),
    "VALUE_TYPE_RULES_check": (validate_column_type, 'VALUE_TYPE_RULES', str),
    "DATA_TYPE_type_check": (validate_column_type, 'DATA_TYPE', str),
    "ORIGINATING_PLANT_TRM_type_check": (validate_column_type, 'ORIGINATING_PLANT_TRM', str),
    "ORIGINATING_DIVISION_type_check": (validate_column_type, 'ORIGINATING_DIVISION', str),
    "PLANT_GROUP_type_check": (validate_column_type, 'PLANT_GROUP', str),
    "MAND_IND_set_check": (validate_column_values_in_set, 'MAND_IND', {'Y', 'N'}),
    "MAND_EMPTY_check": (validate_column_regex, 'MAND_EMPTY', '^[a-zA-Z\\s]*$|^NULL$'),
}

validation_results = {}
passed_counts = {}
failed_counts = {}

for check, (func, column, rule) in validation_checks.items():
    validation_results[check] = func(df, column, rule)
    passed_counts[check] = validation_results[check].sum()
    failed_counts[check] = len(df) - passed_counts[check]

total_rows = len(df)
passed_percentage = {check: (count / total_rows) * 100 for check, count in passed_counts.items()}
failed_percentage = {check: (count / total_rows) * 100 for check, count in failed_counts.items()}

total_validation_percentage = calculate_total_validation_percentage(validation_results)
pod_duplication_percentage = calculate_duplication_percentage(df, 'POD')
completeness_percentage = calculate_completeness(df)

# Collect failed data points for each validation check
failed_data_points = df.copy()
for check, result in validation_results.items():
    failed_data_points[check] = ~result

failed_data_points['Failed_Checks'] = failed_data_points.apply(
    lambda row: [check for check in validation_checks.keys() if row[check]], axis=1
)

failed_data_points = failed_data_points[failed_data_points['Failed_Checks'].map(len) > 0]

valid_data_points = df[~df.index.isin(failed_data_points.index)]

# Layout: Three main sections
st.header("Statistics")

# Gauge Charts for Statistics
col1, col2, col3 = st.columns(3)

with col1:
    fig_gauge_validation = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_validation_percentage,
        title={'text': "Total Validation Percentage"},
        gauge={'axis': {'range': [None, 100]}}
    ))
    fig_gauge_validation.update_layout(width=300, height=300)
    st.plotly_chart(fig_gauge_validation)

st.markdown("<br>", unsafe_allow_html=True)  # Add space between gauges

with col2:
    fig_gauge_pod = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pod_duplication_percentage,
        title={'text': "POD Duplication Percentage"},
        gauge={'axis': {'range': [None, 100]}}
    ))
    fig_gauge_pod.update_layout(width=300, height=300)
    st.plotly_chart(fig_gauge_pod)

st.markdown("<br>", unsafe_allow_html=True)  # Add space between gauges

with col3:
    fig_gauge_completeness = go.Figure(go.Indicator(
        mode="gauge+number",
        value=completeness_percentage,
        title={'text': "Completeness Percentage"},
        gauge={'axis': {'range': [None, 100]}}
    ))
    fig_gauge_completeness.update_layout(width=300, height=300)
    st.plotly_chart(fig_gauge_completeness)

# Show validation results as tables
st.header("Validation Results")

passed_df = pd.DataFrame({
    "Validation Check": list(passed_percentage.keys()),
    "Passed Percentage": list(passed_percentage.values())
})

failed_df = pd.DataFrame({
    "Validation Check": list(failed_percentage.keys()),
    "Failed Percentage": list(failed_percentage.values())
})

# Bar Chart of Validation Results
labels = list(passed_percentage.keys())
passed = list(passed_percentage.values())
failed = list(failed_percentage.values())

fig_validation = go.Figure()
fig_validation.add_trace(go.Bar(
    y=labels,
    x=passed,
    name='Passed',
    orientation='h',
    marker_color='green'
))
fig_validation.add_trace(go.Bar(
    y=labels,
    x=failed,
    name='Failed',
    orientation='h',
    marker_color='red'
))

fig_validation.update_layout(barmode='stack', title="Validation Results", xaxis_title="Percentage", yaxis_title="Validation Check")
st.plotly_chart(fig_validation)

# Download failed data points as CSV
st.header("Failed Data Points")
st.dataframe(failed_data_points)
csv = failed_data_points.to_csv(index=False)
st.download_button(label="Download Failed Data Points as CSV", data=csv, file_name='failed_data_points.csv', mime='text/csv')

# Email section
st.sidebar.title("Send Report via Email")
to_email = st.sidebar.text_input("Recipient Email")
email_subject = st.sidebar.text_input("Email Subject")
email_body = st.sidebar.text_area("Email Body")

if st.sidebar.button("Send Email"):
    if not to_email or not email_subject or not email_body:
        st.sidebar.warning("Please fill in all the email fields.")
    else:
        try:
            # Save the CSV to a temporary file
            temp_csv_path = "/tmp/failed_data_points.csv"
            with open(temp_csv_path, 'w') as f:
                f.write(csv)
            
            send_email(to_email, email_subject, email_body, temp_csv_path)
            st.sidebar.success("Email sent successfully!")
        except Exception as e:
            st.sidebar.error(f"Error sending email: {e}")
