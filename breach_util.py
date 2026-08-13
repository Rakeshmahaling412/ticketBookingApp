from dateutil.relativedelta import relativedelta
from flask_login import current_user

from main.schema.model_all import Breach, DeletedBreaches, LegalentityCompanyMapping, Score, BreachDrafts
from main import logger
from sqlalchemy import Column, Date, Integer, Text, create_engine, inspect, func, asc
import datetime
from typing import List
from cpla_flask_admin.schema.admin import db
from main.schema.profile import Profile
from main.util.rolling_window_util import get_breach_period_window_as_date_objs
from main.util.employee_util import recalculate_recommended_action_for_employee, refresh_breach_data

data_version_dict = {
    'create_time': '%Y-%m-%d, %H:%M:%S"'

}


# A rolling window to chose breaches from 1 Oct-30 Sep (based on today's date)
def get_breach_period(year=None):
    if year:
        breach_period_start = datetime.date(year - 1, 10, 1)
        breach_period_end = datetime.date(year, 9, 30)
        return breach_period_start, breach_period_end
    if datetime.date.today().month < 10:
        breach_period_start = datetime.date(datetime.date.today().year - 1, 10, 1)
    else:
        breach_period_start = datetime.date(datetime.date.today().year, 10, 1)

    return breach_period_start, datetime.date.today()


def jsonify_breach(breach: Breach) -> dict:
    # 1. Breach -> dict
    # 2. Convert python builtin type into readable string field
    # i.e. Datetime -> Datetime string
    breach_dict = {c.key: getattr(breach, c.key)
                   for c in inspect(breach).mapper.column_attrs}
    for k, v in breach_dict.items():
        if isinstance(v, str):
            breach_dict[k] = v.strip()
        if isinstance(v, datetime.datetime) or isinstance(v, datetime.date):
            breach_dict[k] = breach_dict[k].strftime("%Y-%m-%d")
        if isinstance(v, list):  # For those db functions which return list
            breach_dict[k] = [date for date in breach_dict[k]]

    return breach_dict


def get_breaches_by_email(email: str) -> dict:
    dic = {}
    breaches = Breach.query.filter(Breach.email_address == email).all()
    for breach in breaches:
        breach = jsonify_breach(breach)
        dic[breach['policy']] = dic.get(breach['policy'], {})
        dic[breach['policy']][breach['breach_type']] = dic[breach['policy']].get(breach['breach_type'], []) + [breach]
    return dic
    # return [jsonify_breach(breach) for breach in Breach.query.filter(Breach.email_address == email).all()]


def get_frequency_by_breaches_and_email(email: str, breaches: List[str], start_date: datetime.date = None, end_date: datetime.date = None, valid_only = False):

    if valid_only:
        breaches_by_group = db.session.query(Breach.identified_breach_date).filter(Breach.email_address == email,
                                                                         Breach.breach_type.in_(breaches), Breach.breach_score.isnot(None)).all()
    else:
        breaches_by_group = db.session.query(Breach.identified_breach_date).filter(Breach.email_address == email,
                                                                     Breach.breach_type.in_(breaches)).all()

    if not (start_date or end_date):
        start_date, end_date = get_breach_period_window_as_date_objs()

    count = 1

    for breach in breaches_by_group:
        earliest_date = breach[0]
        if start_date <= earliest_date <= end_date:
            count += 1

    return count

def get_breach_by_id(breach_id: int):
    query = db.session.query(Breach).filter(Breach.id == breach_id).first()
    return query

def get_breach_draft_by_id(breach_id: int):
    query = db.session.query(BreachDrafts).filter(BreachDrafts.id == breach_id).first()
    return query


def get_all_breaches_between_dates(employee_email: str, start_date: datetime.date = None, end_date: datetime.date = None, valid_only=False):
    if not (start_date or end_date):
        start_date, end_date = get_breach_period_window_as_date_objs()

    if valid_only:
        breaches = db.session.query(Breach.breach_type, Breach.policy, Breach.identified_breach_date,
                                    Breach.subtype_qa_list).filter(
            Breach.email_address == employee_email,
            Breach.identified_breach_date.isnot(None), Breach.breach_score.isnot(None)
        ).order_by(asc(Breach.create_time)).all()
    else:
        breaches = db.session.query(Breach.breach_type, Breach.policy, Breach.identified_breach_date, Breach.subtype_qa_list).filter(
        Breach.email_address == employee_email,
        Breach.identified_breach_date.isnot(None)
    ).order_by(asc(Breach.create_time)).all()


    date_filtered_breaches = []

    for breach in breaches:
        identified_breach_date = breach[2]
        if start_date <= identified_breach_date <= end_date:
            date_filtered_breaches.append(breach)

    return date_filtered_breaches


def get_employee_from_breach(breach):
    employee_fields = {'email_address',
                       'employee_name',
                       'employee_igg',
                       'job_title',
                       'contract_type',
                       'physical_start_date',
                       'business_unit',
                       'legal_entity',
                       'location',
                       'manager_email_address'}

    employee_dict = {k: v if v else '' for k, v in breach.get_model_dict().items() if k in employee_fields}
    return employee_dict


def get_entity_from_legal_entity(legal_entity: str):
    return Profile.query.filter(Profile.legal_entity == legal_entity).first().profileid


def save_deleted_breach(breach: Breach, session: db.session, delete_reason=None):
    deleted_breach = DeletedBreaches()

    for column in DeletedBreaches.__table__.columns:
        if hasattr(breach, column.name):
            setattr(deleted_breach, column.name, getattr(breach, column.name))

    deleted_breach.deleted_by = current_user.igg
    deleted_breach.delete_reason = delete_reason

    session.add(deleted_breach)
    session.commit()


def get_breach_cumulative_score_by_id(breach_id):
    query = db.session.query(Breach).filter(Breach.id == breach_id).first()
    return query.cumulative_breach_score


def get_additional_recipients_from_score_using_breach_id(breach_id) -> str:
    additional_recipients = ''
    try:
        breach = db.session.query(Breach).filter(Breach.id == breach_id).first()
        category = breach.policy
        breach_type = breach.breach_type
        additional_recipients = db.session.query(Score).filter(Score.breach_type == breach_type, Score.policy == category).first().additional_recipients
        if not additional_recipients:
            additional_recipients = ''
    except Exception as e:
        logger.info("Exception while fetching additional recipients from score table: ", e)
    return additional_recipients


def delete_breaches_by_batch_id(batch_id, session: db.session):
    breaches_to_delete = session.query(Breach).filter(Breach.batch_id == batch_id).all()
    for breach_to_delete in breaches_to_delete:
        session.delete(breach_to_delete)
        session.commit()
        recalculate_recommended_action_for_employee(email_address=breach_to_delete.email_address)
        save_deleted_breach(session=session, breach=breach_to_delete, delete_reason="Deleted by " + current_user.email)

def delete_expired_breaches(db_sess, app_context):
    with app_context:
        today = datetime.datetime.combine(datetime.datetime.today().date(), datetime.datetime.min.time())
        old_breaches = db_sess.query(Breach).filter(
            Breach.identified_breach_date < (today - relativedelta(years=1))
        ).all()

        affected_employees = set()
        for breach in old_breaches:
            affected_employees.add(breach.email_address)

            db_sess.delete(breach)
            db_sess.flush()
            save_deleted_breach(session=db_sess, breach=breach, delete_reason='Auto delete breaches older than 1 year.')
            refresh_breach_data(email_address=breach.email_address, action='delete')

        for email_address in affected_employees:
            recalculate_recommended_action_for_employee(email_address)

        db_sess.commit()
