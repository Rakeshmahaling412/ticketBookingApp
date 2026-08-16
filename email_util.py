import os
import re
import smtplib
import sys
from collections import defaultdict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from urllib.request import ProxyHandler, build_opener, install_opener
import mjml

from main import logger

from configparser import ConfigParser

from main.schema.model_all import EmailTemplate, Score, BreachProcess, Breach, DoNotSendEmailTo, Employee, get_current_cet_time, EmailHistory

from cpla_flask_admin.schema.admin import db

from main.system_extracts.night_batch_utils import db_session, get_recommended_action
from main.util.breach_util import get_breach_by_id, get_breach_cumulative_score_by_id, \
    get_additional_recipients_from_score_using_breach_id
from main.util.email_template_util import get_email_template_by_name
from main.util.employee_util import is_employee_external
from main.util.recommended_actions_util import get_dynammic_recommended_action, get_cnc_approval_flag
from main.util.rolling_window_util import get_breach_period_window_as_date_objs
from main.views.model_employee import EmployeeListView


def get_config_filename():
    config_file = './main/config/email_config.ini'
    if os.environ.get('webenv', '') == 'local':
        config_file = './config/email_config.ini'
    return config_file


def config():
    filename = get_config_filename()
    section = 'prd.email' if os.getenv('webenv') == 'prd' else 'uat.email' if os.getenv(
        'webenv') == 'dev' else 'uat.email' if os.getenv('webenv') == 'uat' else 'local.email'
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db
def read_full_email_config():
    try:
        config = ConfigParser()
        filename = get_config_filename()
        config.read(filename)
        return config
    except FileNotFoundError:
        logger.error("No email config file present. Exiting....")
        sys.exit(-1)

def generate_email_mjml(message, breach_id, domain_address, overview_table=''):
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
         
          <p>For internal reference, please quote case ID: <a href="%domain_address%/breach/details?id=%breach_id%">%breach_id%</a>.</p>
          
          OVERVIEW_TABLE_FOR_MANAGER
        
          This is a system generated email. 
            
         </mj-text>
        </mj-body>
    </mjml>  
    '''

    # body=template
    body = template.replace('CONTENTS_SPLIT_SIGNAL_INSERT_AT_HERE', message).replace("%breach_id%",
                                                                                     str(breach_id)).replace(
        "%domain_address%", str(domain_address)).replace(
        'OVERVIEW_TABLE_FOR_MANAGER', overview_table)

    return body


@db_session
def get_internal_email_template_content(session):
    return session.query(EmailTemplate.email_template_content).filter(
        EmailTemplate.email_template_name == 'ASI_C&C_Notification').scalar()

@db_session
def check_if_email_in_do_not_send_list(session, email):
    return session.query(DoNotSendEmailTo.email).filter(DoNotSendEmailTo.email == email).scalar() == email


def add_failsafe():
    receiver_email = 'anshuman.gogoi@socgen.com'
    receiver_email_cc = 'suv-sanjit.patnaik@socgen.com'
    receiver_email_bcc = ''
    return receiver_email, receiver_email_cc, receiver_email_bcc


def create_msg(email_config: dict, breach_id, breach_score, employee_name, receiver_email,
               receiver_email_cc, receiver_email_bcc, email_content, email_comments_to_staff):

    # Do not send email if receiver is in Do Not Send To list
    if check_if_email_in_do_not_send_list(receiver_email):
        logger.info(f"Receiver Email ({receiver_email}) is in 'Do Not Send Email To' list")
        return None

    msg = MIMEMultipart('related')

    if os.getenv('webenv') == 'prd':
        msg['Subject'] = f"{email_config['subject']} {employee_name} ({receiver_email})"
    else:
        msg['Subject'] = f"[{os.getenv('webenv')}] {email_config['subject']} {employee_name} ({receiver_email})"

    # Do not send email to manager if receiver's manager is in Do Not Send To list
    if check_if_email_in_do_not_send_list(receiver_email_cc):
        logger.info(f"Manager Email ({receiver_email_cc}) is in 'Do Not Send Email To' list")
        receiver_email_cc = ''

    # If employee is external, do not send emails to them
    if is_employee_external(receiver_email):
        receiver_email = ''

    # WARNING, DO NOT SEND TEST EMAILS TO OTHER USERS on local
    if os.getenv('webenv') == 'local':
        receiver_email, receiver_email_cc, receiver_email_bcc = add_failsafe()

    if email_config["other_recipients_in_cc"]:
        receiver_email_cc += f',{email_config["other_recipients_in_cc"]}'

    msg['From'] = email_config['sender_email']

    if not breach_score:
        breach_score = 0

    dynamic_recommended_action = get_dynammic_recommended_action(breach_score)

    msg['To'] = receiver_email if dynamic_recommended_action.email_to_employee else ''

    receiver_email_cc = receiver_email_cc if dynamic_recommended_action.email_to_manager else ''

    # additional_recipients = get_additional_recipients_from_score_using_breach_id(breach_id)

    msg['Cc'] = receiver_email_cc

    msg['Bcc'] = receiver_email_bcc


    email_content = email_content.replace("%email_comments_to_staff%", email_comments_to_staff)

    previous_breaches_overview_table = generate_previous_breaches_overview_table(breach_id,
                                                                                 email_config['domain_address'])
    mjml_template = generate_email_mjml(message=email_content, breach_id=breach_id,
                                        domain_address=email_config['domain_address'],
                                        overview_table=previous_breaches_overview_table)

    # if dynamic_recommended_action.custom_email_alert_template and dynamic_recommended_action.custom_email_alert and dynamic_recommended_action.custom_email_subject:
    #     send_custom_email(dynamic_recommended_action.custom_email_alert_template, dynamic_recommended_action.custom_email_alert, dynamic_recommended_action.custom_email_subject, breach_id)

    msg.preamble = 'Multi-part message in MIME format.'

    html = mjml.mjml_to_html(StringIO(re.sub(r"&(?!amp;)", "&amp;", mjml_template)))
    msg.attach(MIMEText(html['html'], 'html'))
    return msg


def create_preliminary_cnc_msg(breach_id):
    breach_score = get_breach_cumulative_score_by_id(breach_id)
    dynamic_recommended_action = get_dynammic_recommended_action(breach_score)
    return generate_email_using_custom_template(dynamic_recommended_action.custom_email_alert_template,
                                                dynamic_recommended_action.custom_email_alert, dynamic_recommended_action.custom_email_subject,
                                                breach_id, approval_text=True)

def send_custom_email(template, receiver, subject, breach_id):
    send_email(generate_email_using_custom_template(template, receiver, subject, breach_id))


def send_deletion_check_email(triggered_user, breach_id, delete_reason):
    msg = MIMEMultipart('related')
    email_config = config()

    msg['From'] = email_config['sender_email']
    msg['To'] = email_config['culture_conduct_email_dl']

    if os.getenv('webenv') == 'prd':
        msg['Subject'] = f"{email_config['delete_email_subject']} {breach_id}"
    else:
        msg['Subject'] = f"[{os.getenv('webenv')}] {email_config['delete_email_subject']} {breach_id}"


    email_content = f"""
                    <b>{triggered_user}</b> is requesting to delete Breach Case ID: <a href='{email_config['domain_address']}/breach/details?id={breach_id}'>{breach_id}</a> <br/><br/> <b>Reason:</b> <i>{delete_reason}</i>. <br/><br/>
                    Please click <a href='{email_config['domain_address']}/delete_breach?breach_id={breach_id}&delete_reason={delete_reason}'>here</a> to approve to delete this breach case.
                    """

    mjml_template = generate_email_mjml(message=email_content, breach_id=breach_id,
                                        domain_address=email_config['domain_address'])

    html = mjml.mjml_to_html(StringIO(re.sub(r"&(?!amp;)", "&amp;", mjml_template)))
    msg.attach(MIMEText(html['html'], 'html'))

    send_email(msg)

def generate_email_using_custom_template(template, receiver, subject, breach_id, approval_text: bool = False):
    msg = MIMEMultipart('related')
    email_config = config()
    breach = db.session.query(Breach).filter(Breach.id == breach_id).first()
    employee_name = breach.employee_name
    email_content = get_email_template_by_name(template)
    breach_subgroup = 'None'
    breach_subtypes = breach.subtype_qa_list

    # remove subgroup row from email if subgroup is none
    if breach_subtypes is None or len(breach_subtypes) == 0:
        email_content = email_content.replace(
            '<tr><td><strong>Breach Subgroup</strong></td><td>%breach_sub_group%</td></tr>', '')
    else:
        breach_subgroup = '<ul>'
        for items in breach_subtypes:
            tup = eval(items)
            breach_subgroup += f'<li>{tup[1]}</li>'
        breach_subgroup += '</ul>'
    email_content = (email_content.replace("%employee_name%", str(employee_name))
                     .replace("%breach_id%", str(breach_id))
                     .replace("%identified_breach_date%", str(breach.identified_breach_date))
                     .replace("%breach_category%", str(breach.policy))
                     .replace("%breach_type%", str(breach.breach_type))
                     .replace("%breach_sub_group%", str(breach_subgroup))
                     .replace("%breach_score%", str(breach.breach_score))
                     .replace("%breach_date%", ', '.join(dt.strftime('%Y-%m-%d') for dt in breach.breach_dates))
                     .replace("%cumulative_breach_score%", str(breach.cumulative_breach_score))
                     .replace("%recommended_action%", str(breach.recommended_action))
                     .replace("%sensitivity_level%",
                              str(EmployeeListView.get_sensitivity_level(breach.cumulative_breach_score)))
                     .replace("%email_comments_to_staff%", str(breach.email_comments_to_staff) if breach.email_comments_to_staff is not None else '')
                     .replace('%sme_confirmed_breach_score%',
                              str(breach.sme_confirmed_severity) if breach.sme_confirmed_severity is not None else 'N/A')
                     )

    try:
        employee_table_id = db.session.query(Employee.id).filter(Employee.email_address == breach.email_address).scalar()
        if employee_table_id:
            email_content = email_content.replace(f'<td>{employee_name}</td>', f'<td><a href={email_config["domain_address"]}/employee/details/?id={str(employee_table_id)}&url=%2Femployee%2F>{employee_name}</a></td>')
    except Exception:
        pass

    msg['From'] = email_config['sender_email']
    msg['To'] = receiver

    if os.getenv('webenv') == 'prd':
        msg['Subject'] = f"{subject} - {employee_name}"
    else:
        msg['Subject'] = f"[{os.getenv('webenv')}] {subject} - {employee_name}"

    previous_breaches_overview_table = generate_previous_breaches_overview_table(breach_id,
                                                                                 email_config['domain_address'],
                                                                                 to_cnc_team=False)
    if approval_text:
        email_content += f"""
                    <br/><i>Please click <a href='{email_config['domain_address']}/approve_breach?breach_id={breach_id}'>here</a> to approve this breach case</i>.
                    """
    mjml_template = generate_email_mjml(message=email_content, breach_id=breach_id,
                                        domain_address=email_config['domain_address'],
                                        overview_table=previous_breaches_overview_table)

    html = mjml.mjml_to_html(StringIO(re.sub(r"&(?!amp;)", "&amp;", mjml_template)))
    msg.attach(MIMEText(html['html'], 'html'))
    return msg


@db_session
def generate_email_using_breach_email_content(session, breach_id):
    email_config = config()
    breach = session.query(Breach).filter(Breach.id == breach_id).first()
    employee_name = breach.employee_name
    receiver_email = breach.email_address
    receiver_email_cc = breach.manager_email_address
    receiver_email_bcc = ''
    email_content = breach.email_content
    breach_subtypes = breach.subtype_qa_list

    # Get breach_subgroup from Breach Type Frequency from Breach Subtype qa list
    breach_subgroup = 'None'

    # remove subgroup row from email if subgroup is none
    if not breach_subtypes or len(breach_subtypes) == 0:
        email_content = email_content.replace(
            '<tr><td><strong>Breach Subgroup</strong></td><td>%breach_sub_group%</td></tr>', '')
    else:
        breach_subgroup = '<ul>'
        for items in breach_subtypes:
            tup = eval(items)
            breach_subgroup += f'<li>{tup[1]}</li>'
        breach_subgroup += '</ul>'


    email_content = email_content. \
                    replace("%breach_sub_group%", breach_subgroup). \
                    replace("%breach_score%", str(breach.breach_score)). \
                    replace("%cumulative_breach_score%", str(breach.cumulative_breach_score)). \
                    replace("%breach_date%", ', '.join(dt.strftime('%Y-%m-%d') for dt in breach.breach_dates)). \
                    replace("%recommended_action%", str(breach.recommended_action)). \
                    replace('%sme_confirmed_breach_score%',
                            str(breach.sme_confirmed_severity) if breach.sme_confirmed_severity is not None else 'N/A')
                    # replace("%sensitivity_level%", str(EmployeeListView.get_sensitivity_level(breach.cumulative_breach_score)))
    email_comments_to_staff = breach.email_comments_to_staff if breach.email_comments_to_staff is not None else ''
    breach_score = get_breach_cumulative_score_by_id(breach_id)
    cnc_flag = get_cnc_approval_flag(breach.cumulative_breach_score)
    if cnc_flag and (breach.email_status != "Reviewed"):
        msg = create_preliminary_cnc_msg(breach_id)
    else:
        msg = create_msg(email_config, breach_id, breach_score, employee_name, receiver_email,
                         receiver_email_cc, receiver_email_bcc, email_content, email_comments_to_staff)
    return msg


@db_session
def generate_previous_breaches_overview_table(session, breach_id, domain_address, to_cnc_team=False):
    breach = session.query(Breach).filter(Breach.id == breach_id).first()
    receiver_email = breach.email_address
    identified_breach_date = breach.identified_breach_date
    start_date, end_date = get_breach_period_window_as_date_objs(identified_breach_date)
    all_rows = session.query(Breach).filter(Breach.id != breach_id, Breach.email_address == receiver_email, Breach.breach_score >= 0).order_by(Breach.create_time.desc()).all()
    breaches = [row for row in all_rows if start_date <= row.identified_breach_date <= end_date]
    rows = ''

    for breach in breaches:
        if breach.subtype_qa_list is None or len(breach.subtype_qa_list) == 0:
            breach_subgroup = 'None'
        else:
            breach_subgroup = '<ul>'
            for items in breach.subtype_qa_list:
                tup = eval(items)
                breach_subgroup += f'<li>{tup[1]}</li>'
            breach_subgroup += '</ul>'
        row = f'''
        <tr>
            <td><a href="{domain_address}/breach/details?id={breach.id}">{breach.id}</a>
            </td>            
            <td>{breach.policy}</td>
            <td>{breach.breach_type}</td>
            <td>{breach_subgroup}</td>
            <td>{breach.breach_score}</td>
            <td>{breach.cumulative_breach_score}</td>
            <td>{breach.sme_confirmed_severity if breach.sme_confirmed_severity is not None else 'N/A'}</td>
            <td>{breach.identified_breach_date}</td>         
        </tr>
        '''
        rows += row

    table = f'''
        <p><strong>Overview Table of Previous Breaches</strong></p>
        <table>
          <tr>
            <th>Breach ID</th>            
            <th>Breach Category</th>
            <th>Breach Type</th>
            <th>Breach Subgroup</th>   
            <th>Breach Score</th>
            <th>Cumulative Breach Score</th>
            <th>SME Confirmed Breach Score</th>
            <th>Identified Breach Date</th>
                     
          </tr>
          {rows}
        </table>
        <br>
    ''' if len(rows) > 1 else ''
    return table


def send_email(msg):
    if msg is None:
        return

    email_config = config()

    logger.info(f"SMTP Server = {email_config['smtp_server']}, Port = {int(email_config['smtp_port'])}")
    s = smtplib.SMTP(email_config['smtp_server'], int(email_config['smtp_port']))


    cc = msg['Cc'].split(',') if msg['Cc'] is not None else []
    bcc = msg['Bcc'].split(',') if msg['Bcc'] is not None else []
    recipients = msg['To'].split(',') + cc + bcc
    recipients = list(filter(None, recipients))

    try:
        response = s.sendmail(msg['From'], recipients, msg.as_string().encode('utf-8'))
    except Exception as ex:
        logger.error(ex)
    finally:
        db.session.add(EmailHistory(
            email_content=msg.as_string(),
            sender=msg['From'],
            recipients=recipients,
            response_details=str(response)
        ))
        db.session.commit()

    s.quit()


@db_session
def get_email_content(session, template_name):
    email_template = session.query(EmailTemplate).filter(
        EmailTemplate.email_template_name == template_name).first().email_template_content
    return email_template


@db_session
def get_breach_ids_to_send_email(session):
    breaches = session.query(Breach).filter(Breach.email_status.in_(['Reviewed', 'C&C Review'])).all()
    breach_ids = [breach.id for breach in breaches]
    return breach_ids


@db_session
def update_email_sent_status(session, breach_id, msg):
    breach = session.query(Breach).filter(Breach.id == breach_id).first()
    if breach.email_status == 'C&C Review':
        breach.email_status = 'Sent for C&C Review'
    elif breach.email_status == 'Sent for C&C Review':
        breach.email_status = 'Reviewed'
    else:
        breach.email_status = 'Sent'
    breach.email_sent_timestamp = get_current_cet_time()
    if msg:
        breach.email_sent_to = msg['To']
        breach.email_cc = msg['Cc']
    session.commit()
    return breach_id

