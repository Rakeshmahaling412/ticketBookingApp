import datetime
import os
from threading import Thread
from typing import List
from typing import Union

from flask import flash
from flask import request, has_app_context
from flask_admin import expose
from flask_admin.actions import action
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from flask_admin.contrib.sqla.filters import DateEqualFilter
from sqlalchemy import or_, and_, cast, Date, ARRAY

from cpla_flask_admin.schema.admin import db
from cpla_flask_admin.schema.referential import Single
from cpla_flask_admin.util.admin_view_secured import SecuredReferentialView
from cpla_flask_admin.util.wtform_view_resume import view_date, ResumeView
from cpla_flask_admin.util.wtform_zmisc_fp import fields
from cpla_flask_admin.util.wtform_zmisc_text import get_text, string_max
from main import logger
from cpla_flask_admin.util.admin_view_secured import SecuredDataView, extract_entities, SecuredReferentialView
from main.app_routes import delete_breach
from main.schema.model_all import Breach
from main.schema.model_all import Employee
from main.util.breach_subtype_score_util import convert_subtypes_str_lst_to_dict_lst
from main.util.breach_util import get_breach_by_id, get_employee_from_breach, save_deleted_breach
from main.util.email_util import send_deletion_check_email
from main.util.employee_util import get_breach_data, recalculate_recommended_action_for_employee
from main.util.rolling_window_util import get_breach_period_window_as_date_objs
from main.util.user_util import *
from main.util.wtform_select import DynamicSubTypeSubForm
from main.views.model_breach_case import BreachCaseView, CaseDetailCreateForm, \
    EmailWarningCreateForm, EmailWarningDetailForm, CaseDetailDetailForm, CaseAuditDetailForm, \
    EmailWarningEditForm, EmailAuditDetailForm, CaseDetailEditFormFactory

from flask import redirect

def format_linebreak(text):
    maxlineLen, startpos = 128, 0
    remainTextLen = len(text)
    formatText = ''
    while remainTextLen > maxlineLen:
        formatText += text[startpos: startpos + maxlineLen]
        text = text[startpos + maxlineLen:]
        if text == '':
            break
        spacepos = text.index(" ")
        if spacepos != -1:
            formatText += text[0:spacepos] + ' '
            linelen = maxlineLen + spacepos + 1
            text = text[spacepos:]
        else:
            formatText += " "
            linelen = maxlineLen + 1

        formatText += '<br>'
        startpos = 0
        remainTextLen -= linelen

    formatText += text[startpos:]
    return formatText


def view_html_linebreak(path: Union[str, List[str]]):
    return lambda view, context, model, name: ResumeView(model, path) \
        .markup(context, '', lambda d: format_linebreak(get_text(d)))


def view_export_text(path: Union[str, List[str]]):
    return lambda view, context, model, name: ResumeView(model, path) \
        .markup(context, '', lambda d: get_text(d))


def view_dates_as_shortened_string(path: Union[str, List[str]]):
    return lambda view, context, model, name: ResumeView(model, path) \
        .markupLong(context, '', lambda d: True, lambda d, l: string_max(l, 40),
                    lambda d: ', '.join(map(str, d)))


def format_links(links_list):
    links = [
        '<a class="btn btn-primary btn-add" href="{0}" rel="noreferrer">{1}</a>'.format(link, link.rsplit("/", 1)[-1])
        for link in links_list]
    return ''.join(links)


def view_links(path: Union[str, List[str]]):
    return lambda view, context, model, name: ResumeView(model, path) \
        .markup(context, '',
                lambda d: format_links(d))


class FilterByEmail(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            emails = db.session.query(Breach.email_address).distinct().all()
            email_list = [value[0] for value in emails]
            options = [(value, value) for value in email_list]
            return options


class FilterByPolicy(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            policies = db.session.query(Breach.policy).distinct().all()
            policy_list = [value[0] for value in policies]
            options = [(value, value) for value in policy_list]
            return options


class FilterByBreachType(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            breach_types = db.session.query(Breach.breach_type).distinct().all()
            breach_type_list = [value[0] for value in breach_types]
            options = [(value, value) for value in breach_type_list]
            return options


class FilterByStatus(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            statuses = db.session.query(Breach.status).distinct().all()
            status_list = [value[0] for value in statuses]
            options = [(value, value) for value in status_list]
            return options


class FilterByIdentificationMethod(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            identification_methods = db.session.query(Breach.identification_method).distinct().all()
            identification_method_list = [value[0] for value in identification_methods]
            options = [(value, value) for value in identification_method_list]
            return options


class FilterByEmailStatus(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            email_statuses = db.session.query(Breach.email_status).distinct().all()
            email_status_list = [value[0] for value in email_statuses]
            options = [(value, value) for value in email_status_list]
            return options


class FilterByBreachDates(DateEqualFilter):
    def apply(self, query, value, alias=None):
        return query.filter(cast(self.column, ARRAY(Date)).op('&&')([value]))

    def operation(self):
        return 'equals'

class FilterByBU(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            business_units = db.session.query(Breach.business_unit).distinct().all()
            business_unit_list = [value[0] for value in business_units]
            options = [(value, value) for value in business_unit_list]
            return options


class FilterByLegalEntity(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            legal_entities = db.session.query(Breach.legal_entity).distinct().all()
            legal_entity_list = [value[0] for value in legal_entities]
            options = [(value, value) for value in legal_entity_list]
            return options

class BreachDataView(SecuredReferentialView):
    can_create = True
    can_edit = False
    can_view_details = True
    can_delete = False
    page_size = 50
    can_export = True
    action_disallowed_list = ['delete']

    # comment out 'Rating to Severity' - wait for users to confirm the logic of this field

    # breach_case_columns = [Breach.policy, Breach.breach_type, Breach.compliance_taxonomy,
    #                        Breach.employee_name, Breach.business_unit, Breach.identified_breach_date,
    #                        Breach.breach_date, Breach.legal_entity, Breach.location,
    #                        Breach.description, Breach.action, Breach.status, Breach.rating_severity,
    #                        Breach.occurrence,Breach.identification_method,
    #                        Breach.root_cause, Breach.supporting_document_path, Breach.t2eOrem, Breach.licensed_staff,
    #                        Breach.sanction, Breach.regulators_notified, Breach.internal_committee_notified];

    column_labels = {"id": "Breach Case ID","transversal_breach": "Specific / Transversal Breach", "policy": "Breach Category", "type": "Breach Type", "location": "Location",
                     "employee_name": "Employee Name", "employee_igg": "Employee IGG",
                     "manager_email_address": "Manager Email",
                     "breach_score": "Suggested Severity",
                     "sme_confirmed_severity": "SME Confirmed Severity",
                     "business_unit": "BU/SU",
                     "action": "Actions Taken", "occurrence": "Breach Frequency",
                     "last_update_time": "Last Modified",
                     "supporting_document_paths": "Supporting Documents",
                     "root_cause": "Breach Root Cause", "t2eOrem": "T2eOrem(MYCIM) ref.",
                     "regulators_notified": "Reported to Regulator",
                     "batch_id": "Batch ID",
                     "compliance_officer": "Breach Case Inputter",
                     "breach_dates": "Breach Date(s)"}

    column_descriptions = {
        "occurrence": "Count of the same breach identified during the monitoring period",
        "cumulative_breach_score": "Snapshot of 12-Month Rolling Cumulative Breach Score at the time of this case creation",
        "create_time": "Creation Time in CET",
        "last_update_time": "Last Modified Time in CET"
    }
    # column_details_list = [Breach.id, Breach.compliance_officer] + [Breach.policy, Breach.breach_type,
    #                                                         Breach.compliance_taxonomy,
    #                                                         Breach.employee_name, Breach.business_unit,
    #                                                         Breach.identified_breach_date,
    #                                                         Breach.breach_date, Breach.legal_entity, Breach.location, Breach.description,
    #                                                         Breach.action, Breach.status, Breach.rating_severity,
    #                                                         Breach.occurrence,
    #                                                         Breach.identification_method,
    #                                                         Breach.root_cause, Breach.licensed_staff,
    #                                                         Breach.sanction, Breach.regulators_notified,
    #                                                         Breach.internal_committee_notified, ] + [Breach.create_time,
    #                                                                                                  Breach.comments,
    #                                                                                                  Breach.last_update_by,
    #                                                                                                  Breach.last_update_time]

    column_filters = [Breach.id, Breach.compliance_officer,
                      FilterByEmail(column=Breach.email_address, name='Email Address'),
                      Breach.employee_name,
                      Breach.employee_igg,
                      FilterByLegalEntity(column=Breach.legal_entity, name='Legal Entity'),
                      FilterByBU(column=Breach.business_unit, name='Business Unit'),
                      FilterByPolicy(column=Breach.policy, name='Breach Category'),
                      FilterByBreachType(column=Breach.breach_type, name='Breach Type'),
                      Breach.breach_score, Breach.sme_confirmed_severity,
                      Breach.occurrence,
                      Breach.cumulative_breach_score,
                      Breach.identified_breach_date,
                      FilterByBreachDates(column=Breach.breach_dates, name='Breach Date'),
                      FilterByStatus(column=Breach.status, name='Status'),
                      FilterByIdentificationMethod(column=Breach.identification_method, name='Identification Method'),
                      FilterByEmailStatus(column=Breach.email_status, name='Email Status'),
                      Breach.batch_id]

    column_default_sort = ('id', True)  # sort in descending order - latest cases go first

    # # Export everything except comments: This is due to the fact that comments are markup
    column_export_list = ["id", "batch_id", "compliance_officer", "email_address",
                          "employee_name", "employee_igg",
                          "business_unit", "legal_entity", "location", "manager_email_address", "transversal_breach", "sme_confirmed_severity",
                          "policy", "breach_type", "breach_score", "occurrence",
                          "cumulative_breach_score", "description",
                          "identified_breach_date", "breach_dates", "status",
                          "identification_method", "root_cause",
                          "licensed_staff", "reported_to_regulator_date", "email_status",
                          "create_time", "last_update_by",
                          "last_update_time"]
    # column_formatters_export = dict([fields(view_export_text, 'action') + fields(view_export_text, 'description')])
    column_formatters = dict(
        #     fields(view_html, 'email_content') +
        #     fields(view_links, 'supporting_document_paths') +
        #     fields(view_dates_as_shortened_string, 'breach_dates')
        fields((view_date, '%Y-%m-%d %H:%M:%S %p'), "create_time", "last_update_time")
    )

    #
    # form_overrides = {
    #     'comments': HTMLField
    # }

    # TODO:this code is to restrict access per department, for now we will only stop at legal-entity level
    # I will leave this code commented out until we test and we get user approval on UAT
    # def get_query(self):
    #     if current_user.get('roles'):
    #     if current_user.get('roles'):
    #          special_roles = list(filter(lambda role: role == 'special', current_user.roles))
    #          if len(special_roles) > 0:
    #              return super(BreachDataView, self).get_query()
    #
    #     return super(BreachDataView, self).get_query().filter(Breach.local_department == current_user.department)

    def get_query(self):
        profile_name = get_user_profile_name()
        if profile_name == 'Administrator':
            return self.session.query(self.model)

        breach_readable_entities = get_user_breach_readable_entities()
        # breach_readable_region = get_user_breach_readable_regions()
        breach_readable_bpos = get_user_breach_readable_bpos()


        entities_filter = self.model.legal_entity.in_(breach_readable_entities)
        create_by_filter = self.model.create_by == current_user.igg

        # operator ('&&') in postgres to check arrays overlap, that is, have any elements in common?
        # ARRAY[1,4,3] && ARRAY[2,1] → TRUE

        # bpos_filter return TRUE for C&C/ guest (not breach_readable_bpos = TRUE, no bpos checking)

        # bpos_filter = or_(not breach_readable_bpos, self.model.bpo_id.op('&&')(breach_readable_bpos))

        match profile_name:
            case 'Breach Case Inputter (EMEA)':
                print('You are Breach Case Inputter (EMEA)')
                return self.session.query(self.model).filter(create_by_filter)
            case 'Unit Breach Policy Officer (EMEA)':
                print('Unit Breach Policy Officer (EMEA)')
                filter_condition = or_(
                    and_(or_(*[self.model.business_unit.like(f"{business_unit}%") for business_unit in breach_readable_bpos]), entities_filter),
                    create_by_filter
                )
                return self.session.query(self.model).filter(filter_condition)

        return self.session.query(self.model).filter(create_by_filter)


    def is_accessible(self):
        try:
            profile_name = get_user_profile_name()
            self.can_create = True
            self.can_edit = False
            self.can_delete = False
            match profile_name:
                case 'Administrator':
                    self.can_delete = True
                    self.can_edit = True
                    return True
                case 'Breach Case Inputter (EMEA)':
                    self.can_delete = True
                    self.can_edit = True
                    return True
                ############################################################
                case 'Unit Breach Policy Officer (EMEA)':
                    self.can_delete = True
                    self.can_edit = True
                    return True
                ############################################################
            return False
        except NoValidSGIAMProfileException as e:
            logger.error(e)
            return False


    def massive_update_email_status(self, ids, email_status):
        breaches = Breach.query.filter(Breach.id.in_(ids)).all()
        for breach in breaches:
            breach.email_status = email_status
            db.session.add(breach)
        db.session.commit()


    def massive_invalidate_breaches(self, ids):
        breaches = Breach.query.filter(Breach.id.in_(ids)).all()
        for breach in breaches:
            breach.breach_score = None
            breach.occurrence = None
            breach.cumulative_breach_score = None
            breach.status = 'Invalidated'
            breach.last_update_by = current_user.first_name + " " + current_user.last_name
            db.session.commit()
            identified_breach_date = breach.identified_breach_date
            start_date, end_date = get_breach_period_window_as_date_objs(identified_breach_date)
            get_breach_data(breach.email_address, action='delete', start_date=start_date, end_date=end_date)
            recalculate_recommended_action_for_employee(breach.email_address)


    def massive_expire_breaches(self, ids):
        breaches = Breach.query.filter(Breach.id.in_(ids)).all()
        today = datetime.datetime.combine(datetime.datetime.today().date(), datetime.datetime.min.time())
        for breach in breaches:
            breach.breach_score = None
            breach.occurrence = None
            breach.cumulative_breach_score = None
            breach.status = 'Expired'
            breach.last_update_by = current_user.first_name + " " + current_user.last_name
            if breach.comments:
                breach.comments += f"\nInvalidated as case has passed 12-month period on {today.date()}"
            else:
                breach.comments = f"Invalidated as case has passed 12-month period on {today.date()}"
            db.session.commit()
            identified_breach_date = breach.identified_breach_date
            start_date, end_date = get_breach_period_window_as_date_objs(identified_breach_date)
            get_breach_data(breach.email_address, action='delete', start_date=start_date, end_date=end_date)
            recalculate_recommended_action_for_employee(breach.email_address)

    @action('update_open', 'Email Status - Open')
    def action_email_status_update_open(self, ids):
        if not get_user_profile_name() in ['Administrator', 'Unit Breach Policy Officer (EMEA)']:
            flash("Sorry you do not have editing privileges", "error")
            return
        self.massive_update_email_status(ids, 'Open')

    @action('update_reviewed', 'Email Status - Reviewed')
    def action_email_status_update_reviewed(self, ids):
        if not get_user_profile_name() in ['Administrator', 'Unit Breach Policy Officer (EMEA)']:
            flash("Sorry you do not have editing privileges", "error")
            return
        self.massive_update_email_status(ids, 'Reviewed')

    @action('update_closed', 'Email Status - Closed')
    def action_email_status_update_closed(self, ids):
        if not get_user_profile_name() in ['Administrator', 'Unit Breach Policy Officer (EMEA)']:
            flash("Sorry you do not have editing privileges", "error")
            return
        self.massive_update_email_status(ids, 'Closed')

    @action('invalidate_bulk', 'Invalidate Breach')
    def action_invalidate_breaches(self, ids):
        if not get_user_profile_name() in ['Administrator', 'Unit Breach Policy Officer (EMEA)']:
            flash("Sorry you do not have editing privileges", "error")
            return
        self.massive_invalidate_breaches(ids)

    @action('update_status_expired', 'Case Status - Expired')
    def massive_update_status_expired(self, ids):
        if not get_user_profile_name() in ['Administrator', 'CPLE Culture and Conduct Administrator']:
            flash("Sorry you do not have editing privileges", "error")
            return
        self.massive_expire_breaches(ids)



    @property
    def column_list(self):
        # dynamically determine column list based on access right level
        cols = ["id", "batch_id", "compliance_officer", "email_address", "employee_name",
                "employee_igg", "business_unit", "legal_entity", "location", "manager_email_address", "transversal_breach",
                "policy", "breach_type", "breach_score", "sme_confirmed_severity", "occurrence", "cumulative_breach_score",
                "identified_breach_date", "breach_dates",
                "status", "identification_method", "root_cause", "licensed_staff", "regulators_notified",
                "email_status",
                "create_time", "last_update_by", "last_update_time"]
        if has_app_context() and not is_restricted():
            return cols
        restricted_columns = {"breach_score","sme_confirmed_severity",
                              "occurrence",
                              "cumulative_breach_score", "email_status"}
        return filter(lambda col: col not in restricted_columns, cols)

    @property
    def _list_columns(self):
        return self.get_list_columns()

    @_list_columns.setter
    def _list_columns(self, value):
        pass

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/http401/custom-breachlog-view')

    # def on_model_change(self, form, model, is_created):
    #     if is_created:
    #         model.email_content = model.email_content
    #         model.email_status = model.email_status
    #         model.entity = self.getLegalEntityMapping(model.legal_entity)
    #     else:
    #         model.last_update_by = str(current_user)
    #         model.entity = self.getLegalEntityMapping(model.legal_entity)
    #
    #     super(SecuredDataView, self).on_model_change(form, model, is_created)
    #
    # def on_form_prefill(self, form, id):
    #     presingles = get_all_singles()
    #     singles = {}
    #     # drop down box sort by values
    #     for key, value in presingles.items():
    #         if key == 'status':
    #             singles[key] = sorted(value, reverse=True)
    #         # elif key == 'rating_severity':
    #         #    singles[key] = value
    #         else:
    #             singles[key] = sorted(value)
    #
    #     def find_single(tuple):
    #         if tuple[0] == 'entity':
    #             form_choices(form, 'entity', False, tuple[1], [(m, m) for m in extract_entities('data', 'write')])
    #         else:
    #             for key, choices in singles.items():
    #                 if tuple[0] == key:
    #                     # preselect Breach Type choice when edit mode
    #                     if key == 'breach_type':
    #                         form_choices(form, key, True, tuple[1], [(v, v) for v in singles[key]])
    #                         if id != None:
    #                             breach = Breach.query.filter(Breach.id == id).first()
    #                             form.breach_type.data = list(breach.breach_type.split(','))
    #                             form.breach_type.object_data = form.breach_type.data
    #                     else:
    #                         form_choices(form, key, True, tuple[1], [(v, v) for v in singles[key]])
    #                     return
    #
    #     for tuple in form._unbound_fields:
    #         find_single(tuple)
    #
    #     form_trees_refresh(form, 'category')
    #     return form

    @expose('/new/')
    def create_view(self):
        # To define wtform Field object, An instance of CaseDetailForm must be created and Field can be bounded
        self.is_accessible()
        if not self.can_create:
            return self.inaccessible_callback('edit')
        try:
            form = CaseDetailCreateForm()
            email_warning_form = EmailWarningCreateForm()
            restricted = is_restricted()
            return self.render('breach_case_view.html',
                               restricted=restricted,
                               employee_detail_columns=BreachCaseView.employee_detail,
                               is_create=True,
                               breach=Breach,
                               employee=Employee,
                               case_detail_form=form,
                               email_warning_form=email_warning_form,
                               case_detail_columns=BreachCaseView.case_detail_columns,
                               case_audit_trail_columns=BreachCaseView.case_audit_trail_columns,
                               escalation_detail_columns=BreachCaseView.escalation_detail_columns,
                               email_warning_columns=BreachCaseView.email_warning_columns)
        except Exception as e:
            logger.info(str(e))
            return f"Exception {str(e)}"

    @expose('/edit')
    def edit_view(self):
        breach_id = request.args.get('id')
        breach = get_breach_by_id(breach_id=breach_id)
        employee = get_employee_from_breach(breach=breach)

        profile_name = get_user_profile_name()
        if profile_name == 'Breach Case Inputter (EMEA)':
            if breach.create_by == None or breach.create_by != current_user.igg:
                return self.inaccessible_callback('edit')

        restricted = is_restricted()
        updated_case_form, updated_email_form = fill_form_for_edit(breach_data=breach, restricted=restricted)
        # Define customize dynamic form for subtypes
        # subtype_qa_list = [{'label': eval(x)[0], 'q_a': eval(x)[1]} for x in breach.subtype_qa_list]
        subtype_qa_list = convert_subtypes_str_lst_to_dict_lst(breach.subtype_qa_list)
        dynamic_subtypes_form = DynamicSubTypeSubForm(subtypes=subtype_qa_list)
        return self.render('breach_case_view.html',
                           restricted=restricted,
                           employee_detail_columns=BreachCaseView.employee_detail,
                           edit_view=True,
                           breach=Breach,
                           employee=employee,
                           case_detail_form=updated_case_form,
                           case_detail_columns=BreachCaseView.case_detail_edit_columns,
                           case_audit_trail_columns=BreachCaseView.case_audit_trail_columns,
                           dynamic_subtype_form=dynamic_subtypes_form,
                           escalation_detail_columns=BreachCaseView.escalation_detail_columns,
                           email_warning_form=updated_email_form,
                           email_warning_columns=BreachCaseView.email_warning_edit_columns)

    def get_url(self, endpoint, **kwargs):
        if ('edit' in endpoint) or ('details' in endpoint):
            breach_id = kwargs.get('id')
            breach = get_breach_by_id(breach_id=breach_id)
            kwargs['email'] = breach.email_address
        return super(BreachDataView, self).get_url(endpoint, **kwargs)

    @expose('/details')
    def details_view(self):
        self.is_accessible()
        if not self.can_view_details:
            return self.inaccessible_callback('edit')
        breach_id = request.args.get('id')
        breach = get_breach_by_id(breach_id=breach_id)

        if not can_user_view_breach(breach.create_by):
            return self.inaccessible_callback('edit')
        employee = get_employee_from_breach(breach=breach)
        updated_case_form, updated_email_form, updated_case_audit_trail_form, updated_email_audit_trail_form = fill_form_for_detail(
            breach_data=breach)
        subtype_qa_list = convert_subtypes_str_lst_to_dict_lst(breach.subtype_qa_list)
        # Define customize dynamic form for subtypes
        dynamic_subtypes_form = DynamicSubTypeSubForm(subtypes=subtype_qa_list)
        restricted = is_restricted()
        return self.render('breach_case_view.html',
                           restricted=restricted,
                           employee_detail_columns=BreachCaseView.employee_detail,
                           details_view=True,
                           breach=Breach,
                           employee=employee,
                           dynamic_subtype_form=dynamic_subtypes_form,
                           case_detail_form=updated_case_form,
                           case_detail_columns=BreachCaseView.case_detail_details_columns,
                           escalation_detail_columns=BreachCaseView.escalation_detail_columns,
                           email_warning_form=updated_email_form,
                           email_warning_columns=BreachCaseView.email_warning_edit_columns,
                           case_audit_trail_form=updated_case_audit_trail_form,
                           case_audit_trail_columns=BreachCaseView.case_audit_trail_columns,
                           email_audit_trail_form=updated_email_audit_trail_form,
                           email_audit_trail_columns=BreachCaseView.email_audit_trail_columns)

    if os.environ.get('webenv', '') == 'local':
        def delete_model(self, model):
            """
                Delete model.
                :param model:
                    Model to delete
            """
            try:
                self.on_model_delete(model)
                self.session.flush()
                self.session.delete(model)
                self.session.commit()
                if model.email_address:
                    identified_breach_date = model.identified_breach_date
                    start_date, end_date = get_breach_period_window_as_date_objs(identified_breach_date)
                    get_breach_data(model.email_address, action='delete', start_date=start_date, end_date=end_date)
                    recalculate_recommended_action_for_employee(model.email_address)
                save_deleted_breach(model, self.session)
            except Exception as ex:
                if not self.handle_view_exception(ex):
                    # flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
                    # log.exception('Failed to delete record.')
                    pass
                self.session.rollback()

                return False
            else:
                self.after_model_delete(model)

            return None
    else:
        @expose('/delete', methods=['GET'])
        def delete_view(self):
            self.is_accessible()
            if not self.can_delete:
                return self.inaccessible_callback('edit')
            delete_dict = request.args.to_dict()
            to_delete_breach_id = delete_dict['id']
            breach_delete_reason = delete_dict['deleteText']
            user_details = f"{current_user.first_name} {current_user.last_name} ({current_user.email})"

            # send_deletion_check_email(triggered_user=user_details, breach_id=to_delete_breach_id, breach_reason=breach_delete_reason)
            thread = Thread(target=send_deletion_check_email,
                            args=(user_details, to_delete_breach_id, breach_delete_reason))
            thread.start()

            flash(f"Record {request.args.get('id')} will be deleted after post C&C administrator approval.", "success")
            return '', 204


def fill_form_for_edit(breach_data: Breach, restricted=False):
    case_detail_form = CaseDetailEditFormFactory(restricted)
    email_warning_form = EmailWarningEditForm()
    case_detail_form.fill_form(breach_data)

    email_warning_form.recommended_action.data = breach_data.recommended_action
    email_warning_form.email_content.data = breach_data.email_content
    email_status_fields = [option[0] for option in
                           Single.query.with_entities(Single.value).filter(Single.type == 'email_status').all()]
    email_warning_form.email_status.choices = [(v, v) for v in email_status_fields ]
    email_warning_form.email_status.data = breach_data.email_status

    return case_detail_form, email_warning_form


def fill_form_for_detail(breach_data: Breach):
    case_detail_form = CaseDetailDetailForm()
    email_warning_form = EmailWarningDetailForm()
    case_audit_trail_form = CaseAuditDetailForm()
    email_audit_trail_form = EmailAuditDetailForm()

    if breach_data.breach_dates:
        breach_dates_list = [breach_date.strftime("%Y-%m-%d") for breach_date in breach_data.breach_dates]
        breach_dates = ", ".join(breach_dates_list)
    else:
        breach_dates = ""

    supporting_documents_list = breach_data.supporting_document_paths

    if breach_data.supporting_document_paths:
        case_detail_form.supporting_document_paths.data = []
        for file_obj in supporting_documents_list:
            case_detail_form.supporting_document_paths.data.append(f"/file/{file_obj.blob_id}/{file_obj.name}")

    case_detail_form.breach_id.data = breach_data.id
    case_detail_form.breach_type.data = breach_data.breach_type
    case_detail_form.occurrence.data = breach_data.occurrence
    case_detail_form.transversal_breach.data = breach_data.transversal_breach
    case_detail_form.policy.data = breach_data.policy
    case_detail_form.identification_method.data = breach_data.identification_method
    case_detail_form.description.data = breach_data.description
    case_detail_form.cumulative_breach_score.data = breach_data.cumulative_breach_score
    case_detail_form.breach_review_period.data = breach_data.breach_review_period
    case_detail_form.sensitivity_level.data = 'True' if breach_data.cumulative_breach_score is not None and breach_data.cumulative_breach_score >= 9 else 'False'
    case_detail_form.status.data = breach_data.status
    case_detail_form.breach_dates.data = breach_dates
    case_detail_form.identified_breach_date.data = breach_data.identified_breach_date
    case_detail_form.comments.data = breach_data.comments
    case_detail_form.breach_score.data = breach_data.breach_score
    case_detail_form.sme_confirmed_severity.data = breach_data.sme_confirmed_severity
    # case_detail_form.supporting_document_paths.data = breach_data.supporting_document_paths
    case_detail_form.root_cause.data = breach_data.root_cause
    case_detail_form.licensed_staff.data = breach_data.licensed_staff
    case_detail_form.regulators_notified.data = breach_data.regulators_notified
    case_detail_form.reported_to_regulator_date.data = breach_data.reported_to_regulator_date
    case_detail_form.comments.data = breach_data.comments
    case_detail_form.email_comments_to_staff.data = breach_data.email_comments_to_staff
    case_detail_form.action_plan_id.data = breach_data.action_plan_id
    case_detail_form.action_plan_short_description.data = breach_data.action_plan_short_description
    case_detail_form.action_plan_due_date.data = breach_data.action_plan_due_date
    case_detail_form.action_plan_completed_date.data = breach_data.action_plan_completed_date
    case_detail_form.date_sent_to_committee.data = breach_data.date_sent_to_committee
    case_detail_form.committee_name.data = breach_data.committee_name

    email_warning_form.recommended_action.data = breach_data.recommended_action
    email_warning_form.email_content.data = breach_data.email_content
    email_warning_form.email_status.data = breach_data.email_status

    case_audit_trail_form.create_time.data = breach_data.create_time
    case_audit_trail_form.create_by.data = breach_data.create_by
    case_audit_trail_form.batch_id.data = breach_data.batch_id
    case_audit_trail_form.last_update_by.data = breach_data.last_update_by
    case_audit_trail_form.last_update_time.data = breach_data.last_update_time

    email_audit_trail_form.email_sent_timestamp.data = breach_data.email_sent_timestamp
    email_audit_trail_form.email_sent_to.data = breach_data.email_sent_to
    email_audit_trail_form.email_sent_cc.data = breach_data.email_cc

    return case_detail_form, email_warning_form, case_audit_trail_form, email_audit_trail_form
