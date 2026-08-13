import re
from datetime import datetime

import pytz
from flask import has_app_context, current_app
from flask_login import current_user
from sqlalchemy import func, ARRAY, select, and_, cast, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased, declared_attr
from sqlalchemy.sql import case
from sqlalchemy.sql import func as sqlfunc

from cpla_flask_admin.schema.admin import db
from cpla_flask_admin_files.schema_abstract.model_all import EmailAbstract


def get_current_cet_time():
    return (datetime.now(pytz.timezone('CET')).strftime("%Y-%m-%d %H:%M:%S"))


breach_file = db.Table('breach_file',
                       db.Column('breach_id', db.Integer, db.ForeignKey('breach.id')),
                       db.Column('file_id', db.Integer, db.ForeignKey('file.id', ondelete="CASCADE")))


class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email_template_name = db.Column(db.String, unique=True)
    email_template_content = db.Column(db.Text)
    created_time = db.Column(db.DateTime, server_default=func.now(), onupdate=get_current_cet_time, default=get_current_cet_time)


class BatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_extract_category = db.Column(db.String)
    file_name = db.Column(db.String, nullable=False)
    last_update = db.Column(db.DateTime, server_default=func.now(), onupdate=get_current_cet_time, default=get_current_cet_time)
    breach_case_count = db.Column(db.Integer)
    record_count = db.Column(db.Integer)
    # Adding new column for file_blob.id with foreign key constraint
    blob_id = db.Column(db.Integer, db.ForeignKey("file_blob.id", ondelete='CASCADE'))
    blob = db.relationship('FileBlob', cascade="all, delete", uselist=False)

    @hybrid_property
    def last_result(self):
        if has_app_context():
            return f'Loaded: {self.breach_case_count}/{self.record_count}'


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email_address = db.Column(db.String, nullable=False)
    employee_name = db.Column(db.String)
    employee_igg = db.Column(db.String)
    job_title = db.Column(db.String)
    contract_type = db.Column(db.String)
    physical_start_date = db.Column(db.Date)
    business_unit = db.Column(db.String)
    legal_entity = db.Column(db.String)
    location = db.Column(db.String)
    manager_email_address = db.Column(db.String)
    internal_committee_notified = db.Column(db.String)
    breaches = db.relationship('Breach', cascade="all, delete", backref='employee', uselist=True)
    _recommended_action = db.Column('recommended_action', db.String, nullable=True)
    # Used for entity constraint
    entity = db.Column(db.String)
    date_sent_to_disciplinary_committee = db.Column(ARRAY(db.Date), default=[])
    employee_status = db.Column(db.String, default='Active')

    # Refer to Reg-watch for hybrid_property usage

    @hybrid_property
    def cumulative_number_of_breaches(self):
        if has_app_context():
            from main.util.employee_util import get_breaches_for_period_using_dates
            filtered_rows = get_breaches_for_period_using_dates(self.email_address, valid_only=True)
            return len(filtered_rows)

    @hybrid_property
    def breach_period(self):
        if has_app_context():
            from main.util.rolling_window_util import get_rolling_window_as_string
            return get_rolling_window_as_string()

    @hybrid_property
    def number_of_unique_breach_categories(self):
        if has_app_context():
            from main.util.employee_util import get_breaches_for_period_using_dates
            filtered_rows = get_breaches_for_period_using_dates(self.email_address, valid_only=True)
            breachcategories = set()
            breachcategories.update([result.policy for result in filtered_rows])
            return len(breachcategories)

    @hybrid_property
    def number_of_unique_breach_types(self):
        if has_app_context():
            from main.util.employee_util import get_breach_types_in_current_period
            breachtypes = get_breach_types_in_current_period(self.email_address, valid_only=True)
            return len(set(breachtypes))

    @hybrid_property
    def sensitivity_level_current(self):
        if has_app_context():
            from main.util.employee_util import get_breaches_for_period_using_dates
            from main.views.model_employee import EmployeeListView
            breach_data_obj = get_breaches_for_period_using_dates(self.email_address, valid_only=True)
            cumulative_score = 0
            for breach in breach_data_obj:
                cumulative_score += breach.breach_score
            return EmployeeListView.get_sensitivity_level(cumulative_score)

    @hybrid_property
    def total_breach_score(self):
        if has_app_context():
            from main.util.breach_subtype_score_util import get_cumulative_scores_between_dates
            _, cumulative_score, _, _ = get_cumulative_scores_between_dates(email_id=self.email_address,
                                                                            transversal_breach=None,
                                                                            breach_type=None,
                                                                            policy=None, valid_only=True)
            return cumulative_score

    @hybrid_property
    def recommended_action(self):
        return self._recommended_action

    @recommended_action.expression
    def recommended_action(cls):
        return case((cls._recommended_action.is_(None), None), else_=cls._recommended_action)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    transversal_breach = db.Column(db.String)
    breach_type = db.Column(db.String)
    policy = db.Column(db.String)
    score = db.Column(db.Integer, nullable=False)
    hide_from_case_view = db.Column(db.Boolean)
    email_template = db.Column(db.String)
    additional_recipients = db.Column(db.String)
    breach_process_id = db.Column(ARRAY(db.String))
    breach_type_group = db.Column(db.String)
    create_by = db.Column(db.String, nullable=False)
    create_time = db.Column(db.DateTime, server_default=func.now(), default=get_current_cet_time)
    last_update_by = db.Column(db.String, nullable=False)
    last_update_time = db.Column(db.DateTime, onupdate=get_current_cet_time, default=get_current_cet_time)
    freeze_count = db.Column(db.Boolean)


class DoNotSendEmailTo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String)


def is_total_breach_score_present(total_breach_score: str):
    """
    To check if the action for total_breach_score is already defined for the recommended_actions table
    """
    return len(db.session.query(DynamicRecommendedActions).filter(
        DynamicRecommendedActions.total_breach_score == total_breach_score).all()) > 1


class LegalentityCompanyMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sg_legal_entity = db.Column(db.String)
    raw_company_name = db.Column(db.String, unique=True)
    country = db.Column(db.String)


class BreachSubtypeScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    breach_subtype = db.Column(db.String)  # aka answer
    breach_type_group = db.Column(db.String)  # e.g. MT_1
    frequency_count = db.Column(db.Integer)
    score = db.Column(db.Integer, nullable=False)
    hide_from_case_view = db.Column(db.Boolean)
    create_by = db.Column(db.String, nullable=False)
    create_time = db.Column(db.DateTime, server_default=func.now(), default=get_current_cet_time)
    last_update_by = db.Column(db.String, nullable=False)
    last_update_time = db.Column(db.DateTime, onupdate=get_current_cet_time, default=get_current_cet_time)
    question = db.Column(db.String)
    level = db.Column(db.Integer, nullable=False)  # 1, 2, 3

    def __str__(self):
        return self.breach_subtype


class CountryMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alpha2 = db.Column(db.String, nullable=False, unique=True)
    alpha3 = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String)


class BreachProcess(db.Model):
    id = db.Column(db.String, primary_key=True)
    owner_name = db.Column(db.String, nullable=False)
    owner_email_id = db.Column(db.String, nullable=False)
    team_email_id = db.Column(db.String, nullable=False)
    bu_su = db.Column(db.String)


class Mail(EmailAbstract):
    # Inheritance # # # # # # # # # # # # # # # # # # # # #
    __mapper_args__ = {'polymorphic_identity': True}


class BreachColumnsMixin:
    id = db.Column(db.Integer, primary_key=True)
    compliance_officer = db.Column(db.String, nullable=False)
    transversal_breach = db.Column(db.String)
    policy = db.Column(db.String)  # Known as breach category
    breach_type = db.Column(db.String)
    # breach_type_group = db.Column(db.String)

    # Removed field: compliance_taxonomy
    # compliance_taxonomy = db.Column(db.String)

    employee_name = db.Column(db.String)
    email_address = db.Column(db.String)
    employee_igg = db.Column(db.String)
    business_unit = db.Column(db.String)

    identified_breach_date = db.Column(db.Date)  # Single date only, no action here

    # Changed field: breach_date -> breach_dates
    breach_date = db.Column(db.String)  # Will be removed after patching to breach_dates
    breach_dates = db.Column(ARRAY(db.Date))  # Multiple dates = {YYYY-MM-DD, YYYY-MM-DD, ...}

    description = db.Column(db.String)
    action = db.Column(db.String)
    status = db.Column(db.String)
    occurrence = db.Column(db.Integer)
    identification_method = db.Column(db.String)
    root_cause = db.Column(db.String)

    # supporting_documents is deprecated but kept because there are existing values
    supporting_documents = db.Column(db.String)

    # New field: supporting_document_paths: Storing the link directly {/file/{id}}
    # supporting_document_paths = db.Column(ARRAY(db.String))
    @declared_attr
    def supporting_document_paths(self):
        return db.relationship('File', secondary=breach_file)

    action_plan_id = db.Column(db.String)
    action_plan_short_description = db.Column(db.String)
    action_plan_due_date = db.Column(db.Date)
    action_plan_completed_date = db.Column(db.Date)
    date_sent_to_committee = db.Column(db.Date)
    committee_name = db.Column(db.String)
    # If relationship is used:
    # supporting_documents = db.relationship('DocumentBlob', cascade="all,delete", backref='breach', uesList=True)

    # New field: breach_score (new)
    breach_score = db.Column(db.Integer)
    sme_confirmed_severity = db.Column(db.Integer)

    t2eOrem = db.Column(db.String)
    licensed_staff = db.Column(db.String)

    # Removed field: sanction
    # sanction = db.Column(db.String)

    regulators_notified = db.Column(db.String)

    # Removed field: internal_committee_notified (moved to employee table)
    # internal_committee_notified = db.Column(db.String)

    comments = db.Column(db.String)
    # create_by: employee igg
    create_by = db.Column(db.String, nullable=False)
    create_time = db.Column(db.DateTime, server_default=func.now(), default=get_current_cet_time)
    last_update_by = db.Column(db.String, nullable=False)
    last_update_time = db.Column(db.DateTime, onupdate=get_current_cet_time, server_default=func.now(),
                                 default=get_current_cet_time)

    # Fields added for additional employee info
    manager_email_address = db.Column(db.String)
    job_title = db.Column(db.String)
    contract_type = db.Column(db.String)
    physical_start_date = db.Column(db.Date)

    # NF-Security # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    location = db.Column(db.String)
    local_department = db.Column(db.String, nullable=False)
    legal_entity = db.Column(db.String)
    entity = db.Column(db.String)

    # New field: batch_id (id of night batch file)
    batch_id = db.Column(db.String)

    # Email History additions
    email_status = db.Column(db.String)
    email_sent_timestamp = db.Column(db.DateTime)
    email_sent_to = db.Column(db.String)
    email_cc = db.Column(db.String)
    email_comments_to_staff = db.Column(db.Text)

    cumulative_breach_score = db.Column(db.Integer)
    breach_review_period = db.Column(db.String)
    recommended_action = db.Column(db.String)
    email_content = db.Column(db.Text)

    # New field: employee_id
    ''' 
    Pre-requisite:
    1. Add this new field to BD
    2. Populate using Dali API
    3. Relate the employee id to the newly created employee record
    4. Define relationship in model_all
    '''

    @declared_attr
    def employee_id(self):
        return db.Column(db.Integer, db.ForeignKey('employee.id'))

    # New field: reported_to_regulator_date
    reported_to_regulator_date = db.Column(db.Date)
    subtype_qa_list = db.Column(ARRAY(db.String))


class Breach(db.Model, BreachColumnsMixin):
    __tablename__ = 'breach'

    def __init__(self, **kwargs):
        super(Breach, self).__init__(**kwargs)
        # do custom initialization here

    @hybrid_property
    def breach_type_group(self):
        if has_app_context():
            return Score.query.filter(Score.policy == self.policy,
                                      Score.breach_type == self.breach_type, Score.transversal_breach == self.transversal_breach).first().breach_type_group

    @breach_type_group.expression
    def breach_type_group(self):
        return select([Score.breach_type_group]).where(and_(Score.policy == self.policy,
                                                            Score.breach_type == self.breach_type, Score.transversal_breach == self.transversal_breach)).as_scalar()

    @hybrid_property
    def bpo_id(self):
        if has_app_context():
            return Score.query.filter(Score.breach_type == self.breach_type,
                                      Score.policy == self.policy, Score.transversal_breach == self.transversal_breach).first().breach_process_id

    # Hybrid property for SQL-like expression (Parsed to real SQL expression)
    @bpo_id.expression
    def bpo_id(self):
        # create alias because Institution is joined already
        alias_score = aliased(Score)
        return select(alias_score.breach_process_id).where(alias_score.breach_type == self.breach_type,
                                                           alias_score.policy == self.policy, alias_score.transversal_breach == self.transversal_breach).as_scalar()

    def safely_update(self, entity=None):
        analyst = 'Administrator'
        if hasattr(current_app, 'login_manager'):
            analyst = str(current_user)
        if not self.analysts:
            self.analysts = analyst
        elif analyst not in self.analysts:
            self.analysts += ',' + analyst
        self.last_update_by = analyst

        def set_access(object, entity):
            object.entity = entity

        if entity:
            set_access(self, entity)

    def get_model_dict(self):
        return dict((column.name, getattr(self, column.name))
                    for column in self.__table__.columns)


class DeletedBreaches(db.Model, BreachColumnsMixin):
    __tablename__ = 'deleted_breaches'
    supporting_document_paths = None
    deleted_by = db.Column(db.String, nullable=False)
    delete_time = db.Column(db.DateTime, server_default=func.now(), default=get_current_cet_time)
    delete_reason = db.Column(db.String)


class BreachDrafts(db.Model, BreachColumnsMixin):
    __tablename__ = 'breach_drafts'
    supporting_document_paths = None

    @declared_attr
    def id(cls):
        return db.Column(db.String, primary_key=True, default=cls.generate_id)

    @staticmethod
    def generate_id():
        all_ids = db.session.query(BreachDrafts).order_by(BreachDrafts.id.desc()).all()
        all_ids = sorted([int(draft_id.id.split('_')[1]) for draft_id in all_ids])
        if len(all_ids) > 0:
            last_id = all_ids[-1]
            new_id = f'Draft_{last_id + 1}'
        else:
            new_id = 'Draft_1'
        return new_id

    def get_model_dict(self):
        return dict((column.name, getattr(self, column.name))
                    for column in self.__table__.columns)

    @hybrid_property
    def bpo_id(self):
        if has_app_context():
            return Score.query.filter(Score.breach_type == self.breach_type,
                                      Score.policy == self.policy).first().breach_process_id

    # Hybrid property for SQL-like expression (Parsed to real SQL expression)
    @bpo_id.expression
    def bpo_id(self):
        alias_score = aliased(Score)
        return select(alias_score.breach_process_id).where(alias_score.breach_type == self.breach_type,
                                                           alias_score.policy == self.policy).as_scalar()

class DynamicRecommendedActions(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_breach_score = db.Column(db.String)
    email_to_employee = db.Column(db.Boolean)
    email_to_manager = db.Column(db.Boolean)
    cnc_approval_required = db.Column(db.Boolean, default=False)
    custom_email_alert = db.Column(db.String)
    custom_email_alert_template = db.Column(db.String)
    custom_email_subject = db.Column(db.String)
    recommended_action = db.Column(db.String)
    create_by = db.Column(db.String, nullable=False)
    create_time = db.Column(db.DateTime, server_default=func.now(), default=get_current_cet_time)
    last_update_by = db.Column(db.String, nullable=False)
    last_update_time = db.Column(db.DateTime, onupdate=get_current_cet_time, default=get_current_cet_time)

    @hybrid_property
    def number(self):
        match = re.search(r'(\d+)$', self.total_breach_score)
        return int(match.group(1)) if match else 0

    @number.expression
    def number(cls):
        return cast(sqlfunc.substring(cls.total_breach_score, r'(\d+)$'), Integer)


class EmailHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email_content = db.Column(db.Text)
    sender = db.Column(db.String)
    recipients = db.Column(db.String)
    time_sent = db.Column(db.DateTime, server_default=func.now(), default=get_current_cet_time)
    response_details = db.Column(db.Text)
