import datetime
import io
import json
import os
import zlib
from collections import defaultdict
from flask import Blueprint, current_app, request, jsonify, redirect
from flask import send_file, flash
from flask_login import current_user
from sqlalchemy import or_

from cpla_flask_admin.schema.admin import db
from cpla_flask_admin.schema.referential import Single
from cpla_flask_admin_files.schema_abstract.model_all import FileBlob, File
from main import logger

from main.schema.model_all import Score, Breach, BreachDrafts, LegalentityCompanyMapping
from main.system_extracts.email_night_batch import run_email_night_batch
from main.system_extracts.gems_breaches import run_gems_night_batch
from main.system_extracts.mandatory_leave import run_mandatory_leave_night_batch
from main.system_extracts.mandatory_training import run_mandatory_training_night_batch
from main.system_extracts.phishing import run_phishing_parser
from main.system_extracts.process_breach_excel import run_excel_parser
from main.system_extracts.system_extracts_health_report import run_weekly_extract_history_email
from main.util.azure_storage_blob import main_upload_blob_storage
from main.util.breach_subtype_score_util import get_cumulative_scores_between_dates, get_breach_subtypes_options, get_subtypes_qa_list
from main.util.breach_util import get_frequency_by_breaches_and_email, get_entity_from_legal_entity, delete_expired_breaches
from main.util.email_util import get_email_content, generate_email_using_breach_email_content, get_breach_ids_to_send_email, send_email, \
            update_email_sent_status
from main.util.employee_util import get_employee_by_email, create_employee, get_breach_data, \
    recalculate_recommended_action_for_employee, recalculate_recommended_action_for_all_employees, \
    update_expired_breaches, refresh_breaches
from main.util.recommended_actions_util import get_dynammic_recommended_action, get_cnc_approval_flag
from main.util.rolling_window_util import get_breach_period_window_as_date_objs, get_rolling_window_as_string
from main.util.score_util import get_email_template_and_bp_owner, get_all_breach_types_by_group, get_breach_dict
from main.util.user_util import get_user_breach_creatable_bpos
from main.views.model_employee import EmployeeListView
from main.util.breach_util import save_deleted_breach
from main.util.user_util import get_user_profile_name

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Public API
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

app_routes = Blueprint('app_routes', __name__)

# Upload Breach.csv file into azure blob container
@app_routes.route('/upload_breach_azure', methods=['GET'])
def trigger_csv_util():
    main_upload_blob_storage()
    return 'Uploaded Breach Blob file in Azure Storage Container'


@app_routes.route('/files/<blob_id>/system_extracts/<blob_name>', methods=['GET'])
def system_extracts_file_local(blob_id, blob_name):
    if current_app.config['EXTRACT_DOWNLOAD_DISABLED']:
        return redirect('/http404/')
    else:
        blob = FileBlob.query.get(blob_id)
        return send_file(
            io.BytesIO(zlib.decompress(blob.binary_data)),
            as_attachment=True,
            attachment_filename=blob_name)


@app_routes.route('/files/<blob_id>//var/cplauser/mount/<extract_type>/<blob_name>', methods=['GET'])
def system_extracts_file(blob_id, blob_name):
    if current_app.config['EXTRACT_DOWNLOAD_DISABLED']:
        return redirect('/http404/')
    else:
        blob = FileBlob.query.get(blob_id)
        return send_file(
            io.BytesIO(zlib.decompress(blob.binary_data)),
            as_attachment=True,
            attachment_filename=blob_name)


@app_routes.route('/get_breach_dict', methods=['GET'])
def breach_dict():
    return get_breach_dict()


@app_routes.route('/get_employee_by_email', methods=['GET'])
def get_employee():
    try:
        email = request.args.get('email')
        employee_dict = get_employee_by_email(email)
        return json.dumps(employee_dict, allow_nan=True)
    except IndexError:
        return jsonify({})
    except Exception as e:
        return f"Exception {str(e)}"


@app_routes.route('/get_legal_entity_and_location', methods=['GET'])
def get_legal_entity_and_location():
    try:
        email = request.args.get('email')
        employee_dict = get_employee_by_email(email)
        # return json.dumps(employee_dict, allow_nan=True)
        results = db.session.query(LegalentityCompanyMapping.sg_legal_entity,
                                   LegalentityCompanyMapping.country).distinct().all()
        entity_location_list = [{'entity': entity, 'location': location} for entity, location in results]
        employee_entity = {'entity': employee_dict.get('Legal Entity', ''), 'location': employee_dict.get('Location', '')}
        if employee_entity in entity_location_list:
            entity_location_list.remove(employee_entity)
        entity_location_list.insert(0, employee_entity)
        return jsonify(entity_location_list)
    except IndexError:
        return jsonify({})
    except Exception as e:
        return f"Exception {str(e)}"


@app_routes.route('/get_breach_policies_and_types', methods=['GET'])
def get_breach_policies_and_types():
    # breach_creatable_bpos = get_user_breach_creatable_bpos()
    res_dict = defaultdict()
    scores = Score.query.with_entities(Score.transversal_breach, Score.policy, Score.breach_type_group, Score.breach_type).filter(
        Score.hide_from_case_view == False,
        # or_(not breach_creatable_bpos, Score.breach_process_id.op('&&')(breach_creatable_bpos))
    ).order_by(Score.score,
    Score.breach_type).all()
    for transversal_breach, policy, breach_type_group, breach_type in scores:
        if transversal_breach not in res_dict:
           res_dict[transversal_breach] = {}
        if policy not in res_dict[transversal_breach]:
            res_dict[transversal_breach][policy] = []
        res_dict[transversal_breach][policy].append({'breach_type_group': breach_type_group, 'value': breach_type})

    for k, v in res_dict.items():
        for k1, v1 in v.items():
            v[k1] = sorted(v1, key=lambda d: d['value'])

    sorted_dict = {k: dict(sorted(v.items())) for k, v in res_dict.items()}
    return json.dumps(sorted_dict)


@app_routes.route('/get_breach_other_options/<fields>', methods=['GET'])
def get_breach_other_options(fields):
    res_dict = {}
    for field in fields.split('+'):
        res_dict[field] = [option[0] for option in
                           Single.query.with_entities(Single.value).filter(Single.type == field).all()]
        if field in ['identification_method']:
            res_dict[field] = sorted(res_dict[field])
        if field in ['identification_method', 'root_cause', 'licensed_staff', 'regulators_notified']:
            res_dict[field].insert(0, '')
        if field in ['email_status']:
            if 'Sent' in res_dict[field]:
                res_dict[field].remove('Sent')
            if 'Reviewed' in res_dict[field]:
                res_dict[field].remove('Reviewed')
        if field in ['status']:
            res_dict[field][0], res_dict[field][2] = res_dict[field][2], res_dict[field][0]
    return json.dumps(res_dict)


def save_breach(obj):
    form_dict = dict(request.form)
    form_dict['create_by'] = current_user.igg
    form_dict['compliance_officer'] = str(current_user)
    form_dict['last_update_by'] = str(current_user)
    form_dict['local_department'] = str(current_user.department)
    # form_dict['last_update_time'] =
    form_dict['breach_dates'] = request.form.getlist("breach_dates") or []
    form_dict['identified_breach_date'] = form_dict['identified_breach_date'] or None
    form_dict['reported_to_regulator_date'] = form_dict['reported_to_regulator_date'] or None
    form_dict['action_plan_due_date'] = form_dict['action_plan_due_date'] or None
    form_dict['action_plan_completed_date'] = form_dict['action_plan_completed_date'] or None
    form_dict['date_sent_to_committee'] = form_dict['date_sent_to_committee'] or None
    form_dict['subtype_qa_list'] = get_subtypes_qa_list(list(filter(None, request.form.getlist('breach_subtypes'))))
    form_dict['entity'] = get_entity_from_legal_entity(form_dict['legal_entity']) or 'SOCIETE GENERALE'
    form_dict['sme_confirmed_severity'] = form_dict['sme_confirmed_severity'] or None
    if 'breach_subtypes' in form_dict:
        form_dict.pop('breach_subtypes')

    if not form_dict['physical_start_date']:
        form_dict['physical_start_date'] = None

    form_dict.pop('sensitivity_level')
    b = obj(**form_dict)
    b_updated = None
    if obj != BreachDrafts:
        b_updated = save_files_to_obj(uploaded_files=request.files.getlist("fileInput"), breach_obj=b)
    if b_updated:
        db.session.add(b_updated)
    else:
        db.session.add(b)
    # To add data to email content
    breach_subtypes = form_dict['subtype_qa_list']

    # Get breach_subgroup from Breach Type Frequency from Breach Subtype qa list
    breach_subgroup = 'None'

    # remove subgroup row from email if subgroup is none
    if len(breach_subtypes) == 0:
        b.email_content = b.email_content.replace(
            '<tr><td><strong>Breach Subgroup</strong></td><td>%breach_sub_group%</td></tr>', '')
    else:
        breach_subgroup = '<ul>'
        for items in breach_subtypes:
            tup = eval(items)
            breach_subgroup += f'<li>{tup[1]}</li>'
        breach_subgroup += '</ul>'

    b.email_content = b.email_content. \
        replace("%breach_id%", str(b.id)). \
        replace("%identified_breach_date%", str(b.identified_breach_date)). \
        replace("%breach_category%", str(b.policy)). \
        replace("%breach_type%", str(b.breach_type))

    if not b.employee_name:
        b.email_content = b.email_content.replace("%employee_name%", str(b.email_address))
    else:
        b.email_content = b.email_content.replace("%employee_name%", str(b.employee_name))

    # replace("%breach_sub_group%", breach_subgroup). \
    # replace("%breach_score%", str(b.breach_score)). \
    # replace("%cumulative_breach_score%", str(b.cumulative_breach_score)). \
    # replace("%recommended_action%", str(b.recommended_action)). \
    # replace("%sensitivity_level%", str(EmployeeListView.get_sensitivity_level(b.cumulative_breach_score)))
    if obj == Breach:
        create_employee(b.email_address,form_dict)
        recalculate_recommended_action_for_employee(b.email_address)
    if obj == BreachDrafts:
        b.breach_score = None
        b.occurrence = None
        b.cumulative_breach_score = None
    db.session.commit()

@app_routes.route('/create_breach', methods=['POST'])
def create_breach():
    save_breach(Breach)
    return redirect('/breach/')

@app_routes.route('/create_breach_draft', methods=['POST'])
def create_breach_draft():
    save_breach(BreachDrafts)
    return redirect('/breachdrafts/')


# @app_routes.route('/save_to_breach/<breach_draft_id>', methods=['GET'])
# def save_to_breach(breach_draft_id):
#     breach_draft = BreachDrafts.query.filter(BreachDrafts.id == int(breach_draft_id)).first()
#     if breach_draft:
#         # exclude ID
#         breach_draft_data = {key: value for key, value in breach_draft.__dict__.items() if key not in ('id', '_sa_instance_state')}
#         breach = Breach(**breach_draft_data)
#         db.session.add(breach)
#         db.session.commit()
#     return redirect('/breach/')

@app_routes.route('/save_to_breach', methods=['POST'])
def save_to_breach():
    form_dict = dict(request.form)
    breach_draft = BreachDrafts.query.get(request.args.get('id'))
    try:
        edit_breach_obj(form_dict, breach_draft)
        breach_draft = BreachDrafts.query.get(request.args.get('id'))
        # exclude ID
        breach_draft_data = {key: value for key, value in breach_draft.__dict__.items() if key not in ('id', '_sa_instance_state')}
        breach = Breach(**breach_draft_data)
        start_date, end_date = get_breach_period_window_as_date_objs(date=breach.identified_breach_date)
        current_score, cumulative_score, breach_subtype, _ = get_cumulative_scores_between_dates(
            email_id=breach.email_address,
            transversal_breach = breach.transversal_breach,
            breach_type=breach.breach_type,
            policy=breach.policy,
            start_date=start_date,
            end_date=end_date,
            valid_only=True)
        breach_frequency = get_frequency_by_breaches_and_email(email=breach.email_address,
                                                               breaches=get_all_breach_types_by_group(
                                                                   transversal_breach=breach.transversal_breach,
                                                                   policy=breach.policy,
                                                                   breach_type=breach.breach_type
                                                               ),
                                                               start_date=start_date,
                                                               end_date=end_date,
                                                               valid_only=True)
        breach.breach_score = current_score
        breach.cumulative_breach_score = cumulative_score
        if breach.sme_confirmed_severity is not None:
            if breach.breach_score == breach.cumulative_breach_score:
                breach.cumulative_breach_score = breach.sme_confirmed_severity
            else:
                delta = int(breach.sme_confirmed_severity - breach.breach_score)
                breach.cumulative_breach_score = breach.cumulative_breach_score + delta if breach.cumulative_breach_score + delta >= 0 else 0
        breach.occurrence = breach_frequency
        breach.recommended_action = EmployeeListView.get_recommended_action_for_a_period(cumulative_score)
        db.session.add(breach)
        db.session.delete(breach_draft)
    except Exception as e:
        print("exception while saving draft to breach: ", e)
        db.session.rollback()
    db.session.commit()
    return redirect('/breach/')


@app_routes.route('/invalidate_case/<breach_id>', methods=['GET'])
def invalidate_case(breach_id):
    breach = Breach.query.filter(Breach.id == int(breach_id)).first()
    if breach:
        breach.breach_score = None
        breach.occurrence = None
        breach.cumulative_breach_score = None
        breach.last_update_by = current_user.first_name + " " + current_user.last_name
        db.session.commit()
        identified_breach_date = breach.identified_breach_date
        start_date, end_date = get_breach_period_window_as_date_objs(identified_breach_date)
        get_breach_data(breach.email_address, action='delete', start_date=start_date, end_date=end_date)
        recalculate_recommended_action_for_employee(breach.email_address)
    return redirect('/breach/')


def edit_breach_obj(form, obj):
    form_dict = form
    b = obj
    b.manager_email_address = form_dict.get('manager_email_address', b.manager_email_address)
    b.legal_entity=form_dict.get('legal_entity', b.legal_entity)
    # b.location=form_dict.get('location', b.location)
    b.business_unit = form_dict.get('business_unit', b.business_unit)
    b.email_content = form_dict.get('email_content', b.email_content)
    b.email_status = form_dict.get('email_status', b.email_status)
    b.description = form_dict.get('description', )
    b.status = form_dict.get('status', b.status)
    sme_confirmed_severity_updated = False
    if isinstance(obj, BreachDrafts):
        if form_dict.get('sme_confirmed_severity') == '':
            b.sme_confirmed_severity = None
        else:
            b.sme_confirmed_severity = int(form_dict.get('sme_confirmed_severity', b.sme_confirmed_severity))
    else:
        # if sme_confirmed_severity is changed in breach edit
        if b.sme_confirmed_severity == None and form_dict.get('sme_confirmed_severity') == '':
            pass
        elif b.sme_confirmed_severity != form_dict.get('sme_confirmed_severity'):
            if form_dict.get('sme_confirmed_severity') == '':
                    b.cumulative_breach_score = b.cumulative_breach_score - b.sme_confirmed_severity + b.breach_score if b.cumulative_breach_score - b.sme_confirmed_severity + b.breach_score >=0 else 0
            else:
                if b.breach_score == b.cumulative_breach_score:
                    b.cumulative_breach_score = int(form_dict.get('sme_confirmed_severity'))
                else:
                    if b.sme_confirmed_severity is None:
                        delta = int(form_dict.get('sme_confirmed_severity', b.sme_confirmed_severity)) - b.breach_score
                    else:
                        delta = int(form_dict.get('sme_confirmed_severity', b.sme_confirmed_severity)) - b.sme_confirmed_severity
                    b.cumulative_breach_score = b.cumulative_breach_score + delta if b.cumulative_breach_score + delta >=0 else 0
            b.sme_confirmed_severity = int(form_dict.get('sme_confirmed_severity')) if form_dict.get('sme_confirmed_severity') != '' else None
            sme_confirmed_severity_updated = True
    b.comments = form_dict.get('comments', b.comments)
    b.identification_method = form_dict.get('identification_method', b.identification_method)
    b.root_cause = form_dict.get('root_cause', b.root_cause)
    b.licensed_staff = form_dict.get('licensed_staff', b.licensed_staff)
    b.regulators_notified = form_dict.get('regulators_notified', b.regulators_notified)
    b.email_comments_to_staff = form_dict.get('email_comments_to_staff', b.email_comments_to_staff)
    b.action_plan_id = form_dict.get('action_plan_id', b.action_plan_id)
    b.action_plan_short_description = form_dict.get('action_plan_short_description', b.action_plan_short_description)
    b.committee_name = form_dict.get('committee_name', b.committee_name)

    reported_to_regulator_date = form_dict.get('reported_to_regulator_date', b.reported_to_regulator_date)
    action_plan_due_date = form_dict.get('action_plan_due_date', b.action_plan_due_date)
    action_plan_completed_date = form_dict.get('action_plan_completed_date', b.action_plan_completed_date)
    date_sent_to_committee = form_dict.get('date_sent_to_committee', b.date_sent_to_committee)

    # date can be empty string
    b.reported_to_regulator_date = reported_to_regulator_date if reported_to_regulator_date else None
    b.action_plan_due_date = action_plan_due_date if action_plan_due_date else None
    b.action_plan_completed_date = action_plan_completed_date if action_plan_completed_date else None
    b.date_sent_to_committee = date_sent_to_committee if date_sent_to_committee else None
    if not isinstance(obj, BreachDrafts):
        save_files_to_obj(uploaded_files=request.files.getlist("fileInput"), breach_obj=b)
    db.session.commit()
    if sme_confirmed_severity_updated and not isinstance(obj, BreachDrafts):
        identified_breach_date = b.identified_breach_date
        start_date, end_date = get_breach_period_window_as_date_objs(identified_breach_date)
        get_breach_data(b.email_address, action='delete', start_date=start_date, end_date=end_date)
        recalculate_recommended_action_for_employee(b.email_address)

@app_routes.route('/edit_breach', methods=['POST'])
def edit_breach():
    form_dict = dict(request.form)
    b = Breach.query.get(request.args.get('id'))
    edit_breach_obj(form_dict, b)
    return redirect('/breach/')


@app_routes.route('/edit_breach_draft', methods=['POST'])
def edit_breach_draft():
    form_dict = dict(request.form)
    b = BreachDrafts.query.get(request.args.get('id'))
    edit_breach_obj(form_dict, b)
    return redirect('/breach/')


def save_files_to_obj(uploaded_files, breach_obj: Breach):
    if not uploaded_files:
        return None
    for uploaded_file in uploaded_files:
        if not uploaded_file.filename:
            continue
        file_binary = zlib.compress(uploaded_file.read())
        file_for_upload = File(blob=FileBlob(binary_data=file_binary), name=uploaded_file.filename)
        remove_duplicate_file(uploaded_file=file_for_upload, breach_file_list=breach_obj.supporting_document_paths)
        db.session.add(file_for_upload)
        db.session.commit()
        breach_obj.supporting_document_paths.append(file_for_upload)
    return breach_obj


def remove_duplicate_file(uploaded_file, breach_file_list):
    i = 0
    for breach_file in breach_file_list:
        if uploaded_file.name == breach_file.name:
            breach_file_list.remove(breach_file)
        i += 1


@app_routes.route('/get_breach_scores_and_frequency', methods=['POST'])
def get_breach_scores_and_frequency():
    request_json = request.get_json()
    employee_email = request_json['employee_email']
    breach_type = request_json['breach_type']
    policy = request_json['policy']
    transversal_breach = request_json['transversal_breach']
    # breach_dates = request_json['breach_dates']
    identified_breach_date = request_json['identified_breach_date']
    start_date, end_date = None, None
    try:
        identified_breach_date = datetime.datetime.strptime(identified_breach_date, "%Y-%m-%d")
        start_date, end_date = get_breach_period_window_as_date_objs(date=identified_breach_date)
    except Exception as e:
        logger.error(e)

    breach_score, cumulative_score, subtype, subtype_id = get_cumulative_scores_between_dates(email_id=employee_email,
                                                                                              transversal_breach=transversal_breach,
                                                                                              breach_type=breach_type,
                                                                                              policy=policy,
                                                                                              start_date=start_date,
                                                                                              end_date=end_date,
                                                                                              valid_only=True)
    breach_frequency = get_frequency_by_breaches_and_email(email=employee_email,
                                                           breaches=get_all_breach_types_by_group(transversal_breach=transversal_breach,
                                                                                                  policy=policy,
                                                                                                  breach_type=breach_type
                                                                                                  ),
                                                           start_date=start_date,
                                                           end_date=end_date,
                                                           valid_only=True)
    breach_review_period = get_rolling_window_as_string(date=identified_breach_date) if isinstance(identified_breach_date, datetime.date) else get_rolling_window_as_string()
    return {'breach_frequency': breach_frequency, 'breach_score': breach_score, 'cumulative_score': cumulative_score,
            'breach_subtype': subtype, 'subtype_id': subtype_id, 'breach_review_period': breach_review_period}


@app_routes.route('/get_email_details', methods=['POST'])
def get_email_details():
    request_json = request.get_json()

    breach_type = request_json['breach_type']
    policy = request_json['policy']
    transversal_breach = request_json['transversal_breach']
    total_score = int(request_json['cumulative_score'])

    email_template, breach_process_owner = get_email_template_and_bp_owner(transversal_breach=transversal_breach, policy=policy, breach_type=breach_type)
    recommended_action = get_dynammic_recommended_action(score=total_score).recommended_action

    email_content = get_email_content(email_template)

    return {'email_template': email_template, 'recommended_action': recommended_action,
            'breach_process_owner': breach_process_owner, 'email_content': email_content}


@app_routes.route('/delete_breach', methods=['GET'])
def delete_breach():
    breach_id = request.args.get('breach_id')
    delete_reason = request.args.get('delete_reason')
    if get_user_profile_name() in ['Administrator', 'Unit Breach Policy Officer (EMEA)']:
        breach = Breach.query.filter(Breach.id == int(breach_id)).first()
        if breach:
            try:
                db.session.flush()
                db.session.delete(breach)
                db.session.commit()
                if breach.email_address:
                    identified_breach_date = breach.identified_breach_date
                    start_date, end_date = get_breach_period_window_as_date_objs(identified_breach_date)
                    get_breach_data(breach.email_address, action='delete', start_date=start_date, end_date=end_date)
                    recalculate_recommended_action_for_employee(breach.email_address)
                save_deleted_breach(breach=breach, session=db.session, delete_reason=delete_reason)
                flash(f"{breach_id} has been deleted", "success")

            except Exception as ex:
                if not db.handle_view_exception(ex):
                    pass
                db.session.rollback()

                flash(f"{breach_id} could not be deleted", "error")
        else:
            flash(f"{breach_id} could not be deleted", "error")
    else:
        flash("Sorry you have insufficient permissions to perform this action.", "error")

    return redirect('/breach')


@app_routes.route('/approve_breach', methods=['GET'])
def approve_breach():
    breach_id = request.args.get('breach_id')
    if get_user_profile_name() in ['Administrator', 'Unit Breach Policy Officer (EMEA)']:
        breach = Breach.query.filter(Breach.id == int(breach_id)).first()
        if breach:
            try:
                update_email_sent_status(breach_id, msg=None)
                flash(f"Breach ID: {breach_id} has been approved", "success")

            except Exception as ex:
                logger.error(ex)
                flash(f"Breach ID: {breach_id} could not be approved", "error")
        else:
            flash(f"Breach ID: {breach_id} could not be approved", "error")
    else:
        flash("Sorry you have insufficient permissions to perform this action.", "error")

    return redirect('/breach')


@app_routes.route('/cnc_approval_flag', methods=['GET'])
def cnc_approval_flag():
    logger.info(request.args.__dict__)
    return {'cnc_flag': get_cnc_approval_flag(int(request.args.get('total_score')))}


@app_routes.route('/send_test_email')
def send_test_email():
    class DummyContext:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            logger.info('exit')

    dummy_context = DummyContext()
    return run_email_night_batch(dummy_context)


class DummyContext:

    def __init__(self, job_name):
        self.job_name = job_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info(f'{self.job_name} job complete')


@app_routes.route('/run_excel_parser')
def excel_parser():
    return run_excel_parser(db.session, app_context=DummyContext(job_name="Excel Parser"))


@app_routes.route('/test_phishing')
def test_phishing():
    logger.info("os.environ.get('platform', ''): ", os.environ.get('platform', ''))
    return run_phishing_parser(app_context=DummyContext(job_name="Phishing Parser"))
    # return run_phishing_night_batch(app_context=DummyContext(job_name="Phishing"))

@app_routes.route('/send_extract_email')
def send_extract_email():
    return run_weekly_extract_history_email(db.session, app_context=DummyContext(job_name="Extract History Email"))


@app_routes.route('/test_blockleave')
def test_blockleave():
    logger.info("os.environ.get('platform', ''): ", os.environ.get('platform', ''))
    return run_mandatory_leave_night_batch(app_context=DummyContext(job_name="Block Leave"))


@app_routes.route('/test_mandate_training')
def test_mandate_training():
    logger.info("os.environ.get('platform', ''): ", os.environ.get('platform', ''))
    return run_mandatory_training_night_batch(app_context=DummyContext(job_name="Mandatory Training"))


@app_routes.route('/test_mandate_training/<country_name>')
def test_mandate_training_china(country_name):
    logger.info("os.environ.get('platform', ''): ", os.environ.get('platform', ''))
    return run_mandatory_training_night_batch(country=country_name, app_context=DummyContext(job_name="Mandatory Training China"))


@app_routes.route('/test_gems')
def test_gems():
    logger.info("os.environ.get('platform', ''): ", os.environ.get('platform', ''))
    return run_gems_night_batch(app_context=DummyContext(job_name="GEMS"))


@app_routes.route('/test_gems_with_date/<custom_date>')
def test_gems_with_custom_date(custom_date):
    logger.info("os.environ.get('platform', ''): ", os.environ.get('platform', ''))
    return run_gems_night_batch(custom_date=custom_date, app_context=DummyContext(job_name="GEMS"))


@app_routes.route('/test_gems/<country_name>')
def test_gems_china(country_name):
    logger.info("os.environ.get('platform', ''): ", os.environ.get('platform', ''))
    return run_gems_night_batch(country=country_name, app_context=DummyContext(job_name="GEMS China"))


@app_routes.route('/get_breach_subtypes_options', methods=['GET'])
def get_breach_subtype():
    res = get_breach_subtypes_options(request.args.get('group'))
    return jsonify(res)


@app_routes.route('/recalculate_recommended_action')
def recalculate_recommended_action():
    class DummyContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            logger.info('exit')

    dummy_context = DummyContext()
    recalculate_recommended_action_for_all_employees(dummy_context)
    return "recalculate_recommended_action done"


@app_routes.route('/expire_old_breaches', methods=['GET'])
def expire_old_breaches():
    if get_user_profile_name() != 'Administrator':
        return "<h1> This endpoint is only for Admins <h1>"
    update_expired_breaches(app_context=DummyContext(job_name="Expire Old Breaches"), db_sess=db.session)
    return jsonify({"status": "success", "data": "Expired breaches have been successfully invalidated"}), 200


@app_routes.route('/refresh_all_breaches', methods=['GET'])
def refresh_all_breaches():
    if get_user_profile_name() != 'Administrator':
        return "<h1> This endpoint is only for Admins <h1>"
    refresh_breaches(app_context=DummyContext(job_name="Refresh All Breaches"), db_sess=db.session)
    return jsonify({"status": "success", "data": "All breaches have been refreshed and scores/frequencies have been re-computed. No breaches have been expired."}), 200

@app_routes.route('/delete_old_breaches', methods=['GET'])
def delete_old_breaches():
    if get_user_profile_name() != 'Administrator':
        return "<h1> This endpoint is only for Admins <h1>"
    delete_expired_breaches(app_context=DummyContext(job_name="Delete Old Breaches"), db_sess=db.session)
    return jsonify({"status": "success", "data": "Expired breaches have been successfully deleted"}), 200
