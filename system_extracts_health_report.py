import datetime
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO

import mjml

from main import logger
from main.schema.model_all import BatchHistory
from main.util.email_util import config, read_full_email_config, send_email

email_config = read_full_email_config()
def get_weekly_extract_history_status(db_session):
    # batches = db_session.query(BatchHistory).all()
    batches = db_session.query(BatchHistory).filter(BatchHistory.last_update >= datetime.datetime.today().date() - datetime.timedelta(days=7)).order_by(BatchHistory.last_update.desc()).all()
    return batches

def generate_health_check_table(batches):

    table = '''<br>
            <table>
            <tr>
            <th>Batch ID</th>
            <th>Extract Category</th>
            <th>File Name</th>
            <th>Last Update</th>
            <th>Last Result</th>
            </tr>
            '''
    for batch in batches:
        td = f'''<tr>
            <td>{batch.id}</td>
            <td>{batch.file_extract_category}</td>
            <td>{os.path.basename(batch.file_name)}</td>
            <td>{batch.last_update}</td>
            <td>{batch.last_result}</td>
            </tr>
            '''
        table += td
    table += '</table>'

    return table

def email_content(batches):
    email_content = f'''
                    Please find the weekly extract history report for Breach Log.<br>
                    {generate_health_check_table(batches)}<br>
                    This is a system generated email.
                    '''
    return email_content

def generate_email_mjml(message):
    template = '''
    <mjml>
        <mj-head>
            <mj-style>
                .hide-link a { 
                  color: black !important; 
                  text-decoration: none !important; 
                }
                table {

                  border-collapse: collapse;
                  width: 80%;
                }

                td, th {
                  border: 1px solid #dddddd;
                  text-align: left;
                  padding: 4px;
                }
                ol{
                    margin: 0px;
                }

                tr:nth-child(even) {
                  background-color: #dddddd;
                }
            </mj-style>
        </mj-head>
        <mj-body background-color="white" width="800px">
         <mj-text font-size="14px" color="black" font-family="Source Sans Pro" align="left">

         CONTENTS_SPLIT_SIGNAL_INSERT_AT_HERE

         </mj-text>
        </mj-body>
    </mjml>  
    '''
    body = template.replace('CONTENTS_SPLIT_SIGNAL_INSERT_AT_HERE', message)

    return body

def send_extract_history_email(batches):
    msg = MIMEMultipart('related')
    msg['From'] = email_config.get('extract_health.email', 'email_sender')
    msg['To'] = email_config.get('extract_health.email', 'email_receiver')
    msg['Cc'] = email_config.get('extract_health.email', 'email_cc')
    msg['Bcc'] = email_config.get('extract_health.email', 'email_bcc')
    msg['Subject'] = email_config.get('extract_health.email', 'subject') + ' - ' + str(datetime.datetime.today().date())
    if os.getenv('webenv') == 'prd':
        msg['Subject'] = f"{msg['Subject']}"
    else:
        msg['Subject'] = f"[{os.getenv('webenv')}] {msg['Subject']}"
    content = email_content(batches)
    mjml_template = generate_email_mjml(message=content)
    html = mjml.mjml_to_html(StringIO(re.sub(r"&(?!amp;)", "&amp;", mjml_template)))
    msg.attach(MIMEText(html['html'], 'html'))
    # logger.info(msg)
    send_email(msg)


def run_weekly_extract_history_email(db_session, app_context):
    with app_context:
        logger.info('Sending Extract History Email...')
        send_extract_history_email(get_weekly_extract_history_status(db_session))
        logger.info('Completed Sending Extract History Email.')
        return 'Completed'
# send_health_check_email()