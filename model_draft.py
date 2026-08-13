from flask import request, has_app_context
from flask_admin import expose
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from sqlalchemy import or_, and_, cast, func, Integer, literal, desc

from cpla_flask_admin.schema.admin import db
from main import logger
from main.util.breach_subtype_score_util import convert_subtypes_str_lst_to_dict_lst
from main.util.breach_util import get_employee_from_breach, \
    get_breach_draft_by_id

from main.util.user_util import *
from main.util.wtform_select import DynamicSubTypeSubForm
from main.views.model_breach_case import BreachCaseView

from main.schema.model_all import BreachDrafts
from main.views.model_breach import BreachDataView, \
    FilterByBreachDates, fill_form_for_edit, fill_form_for_detail

class FilterByEmailStatus(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            email_statuses = db.session.query(BreachDrafts.email_status).distinct().all()
            email_status_list = [value[0] for value in email_statuses]
            options = [(value, value) for value in email_status_list]
            return options

class FilterByStatus(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            statuses = db.session.query(BreachDrafts.status).distinct().all()
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
            identification_methods = db.session.query(BreachDrafts.identification_method).distinct().all()
            identification_method_list = [value[0] for value in identification_methods]
            options = [(value, value) for value in identification_method_list]
            return options


class FilterByBreachType(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            breach_types = db.session.query(BreachDrafts.breach_type).distinct().all()
            breach_type_list = [value[0] for value in breach_types]
            options = [(value, value) for value in breach_type_list]
            return options



class FilterByEmail(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            emails = db.session.query(BreachDrafts.email_address).distinct().all()
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
            policies = db.session.query(BreachDrafts.policy).distinct().all()
            policy_list = [value[0] for value in policies]
            options = [(value, value) for value in policy_list]
            return options

class FilterByLegalEntity(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            legal_entities = db.session.query(BreachDrafts.legal_entity).distinct().all()
            legal_entity_list = [value[0] for value in legal_entities]
            options = [(value, value) for value in legal_entity_list]
            return options

class FilterByBU(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            business_units = db.session.query(BreachDrafts.business_unit).distinct().all()
            business_unit_list = [value[0] for value in business_units]
            options = [(value, value) for value in business_unit_list]
            return options


class DraftDataView(BreachDataView):
    can_create = False
    can_edit = True
    can_view_details = True
    can_delete = True
    page_size = 50
    can_export = True


    column_filters = ["id", "compliance_officer",
                      FilterByEmail(column=BreachDrafts.email_address, name='Email Address'),
                      "employee_name",
                      "employee_igg",
                      FilterByLegalEntity(column=BreachDrafts.legal_entity, name='Legal Entity'),
                      FilterByBU(column=BreachDrafts.business_unit, name='Business Unit'),
                      FilterByPolicy(column=BreachDrafts.policy, name='Breach Category'),
                      FilterByBreachType(column=BreachDrafts.breach_type, name='Breach Type'),
                      "breach_score",
                      "occurrence",
                      "cumulative_breach_score",
                      "identified_breach_date",
                      FilterByBreachDates(column=BreachDrafts.breach_dates, name='Breach Date'),
                      FilterByStatus(column=BreachDrafts.status, name='Status'),
                      FilterByIdentificationMethod(column=BreachDrafts.identification_method, name='Identification Method'),
                      FilterByEmailStatus(column=BreachDrafts.email_status, name='Email Status'),
                      "batch_id"]

    column_default_sort = ('id', True)  # sort in descending order - latest cases go first

    column_export_list = ["id", "batch_id", "compliance_officer", "email_address",
                          "employee_name", "employee_igg",
                          "business_unit", "legal_entity", "location", "manager_email_address", "transversal_breach",
                          "sme_confirmed_severity",
                          "policy", "breach_type", "breach_score", "occurrence",
                          "cumulative_breach_score", "description",
                          "identified_breach_date", "breach_dates", "status",
                          "identification_method", "root_cause",
                          "licensed_staff", "reported_to_regulator_date", "email_status",
                          "create_time", "last_update_by",
                          "last_update_time"]

    def init_actions(self):
        super().init_actions()

        not_applicable_actions = ['invalidate_bulk', 'update_open', 'update_reviewed', 'update_closed']
        self._actions = [action for action in self._actions if action[0] not in not_applicable_actions]
        for action in not_applicable_actions:
            if action in self._actions_data:
                del self._actions_data[action]

    def is_accessible(self):
        try:
            profile_name = get_user_profile_name()
            if profile_name in ['Administrator', 'Breach Case Inputter (EMEA)', 'Unit Breach Policy Officer (EMEA)']:
                return True
            return False
        except NoValidSGIAMProfileException as e:
            logger.error(e)
            return False

    def get_query(self):
        profile_name = get_user_profile_name()
        if profile_name == 'Administrator':
            return self.session.query(self.model).order_by(desc(cast(func.substr(self.model.id, func.position(literal('_').op('IN')(self.model.id)) + 1), Integer)))

        breach_readable_entities = get_user_breach_readable_entities()
        breach_readable_bpos = get_user_breach_readable_bpos()

        entities_filter = self.model.legal_entity.in_(breach_readable_entities)
        create_by_filter = self.model.create_by == current_user.igg

        match profile_name:
            case 'Breach Case Inputter (EMEA)':
                return self.session.query(self.model).filter(create_by_filter).order_by(cast(func.substr(self.model.id, func.position(literal('_').op('IN')(self.model.id)) + 1), Integer), desc(self.model.id))

            case 'Unit Breach Policy Officer (EMEA)':
                filter_condition = or_(
                    and_(or_(*[self.model.business_unit.like(f"{business_unit}%") for business_unit in
                           breach_readable_bpos]), entities_filter),
                    create_by_filter
                )
                return self.session.query(self.model).filter(filter_condition).order_by(cast(func.substr(self.model.id, func.position(literal('_').op('IN')(self.model.id)) + 1), Integer), desc(self.model.id))

        return self.session.query(self.model).filter(create_by_filter).order_by(cast(func.substr(self.model.id, func.position(literal('_').op('IN')(self.model.id)) + 1), Integer), desc(self.model.id))


    @property
    def column_list(self):
        # dynamically determine column list based on access right level
        cols = ["id", "batch_id", "compliance_officer", "email_address", "employee_name",
                "employee_igg", "business_unit", "legal_entity", "location", "manager_email_address",
                "policy", "breach_type", "breach_score", "occurrence", "cumulative_breach_score",
                "identified_breach_date", "breach_dates",
                "status", "identification_method", "root_cause", "licensed_staff", "regulators_notified",
                "email_status",
                "create_time", "last_update_by", "last_update_time"]
        if has_app_context() and not is_restricted():
            return cols
        restricted_columns = {"breach_score",
                              "occurrence",
                              "cumulative_breach_score", "email_status"}
        return filter(lambda col: col not in restricted_columns, cols)

    @property
    def _list_columns(self):
        return self.get_list_columns()

    @_list_columns.setter
    def _list_columns(self, value):
        pass

    @expose('/edit')
    def edit_view(self):
        self.is_accessible()
        if not self.can_edit:
            return self.inaccessible_callback('edit')
        breach_id = request.args.get('id')
        breach = get_breach_draft_by_id(breach_id=breach_id)
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
                           draft_view=True,
                           breach=BreachDrafts,
                           employee=employee,
                           case_detail_form=updated_case_form,
                           case_detail_columns=BreachCaseView.case_detail_edit_columns,
                           case_audit_trail_columns=BreachCaseView.case_audit_trail_columns,
                           dynamic_subtype_form=dynamic_subtypes_form,
                           escalation_detail_columns=BreachCaseView.escalation_detail_columns,
                           email_warning_form=updated_email_form,
                           email_warning_columns=BreachCaseView.email_warning_edit_columns)

    def get_url(self, endpoint, **kwargs):
        # if ('edit' in endpoint) or ('details' in endpoint):
        #     breach_id = kwargs.get('id')
        #     breach = get_breach_by_id(breach_id=breach_id)
        #     kwargs['email'] = breach.email_address
        return super(BreachDataView, self).get_url(endpoint, **kwargs)
        # pass
    @expose('/details')
    def details_view(self):
        self.is_accessible()
        if not self.can_view_details:
            return self.inaccessible_callback('edit')
        breach_id = request.args.get('id')
        breach = get_breach_draft_by_id(breach_id=breach_id)

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
                           draft_view=True,
                           breach=BreachDrafts,
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

    @expose('/delete', methods=['POST'])
    def delete_view(self):
        return super(BreachDataView, self).delete_view()
