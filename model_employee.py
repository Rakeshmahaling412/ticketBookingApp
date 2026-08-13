from datetime import date
from typing import List
from typing import Union

from flask import request, has_app_context
from flask_admin import expose
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list
from sqlalchemy import or_, null, and_
from werkzeug.utils import redirect

from cpla_flask_admin.schema.admin import db
from cpla_flask_admin.util.admin_view_secured import SecuredReferentialView
from cpla_flask_admin.util.admin_view_secured import form_choices, get_all_singles
from cpla_flask_admin.util.wtform_view_resume import ResumeView
from main.schema.model_all import Employee, DynamicRecommendedActions
from main.util.breach_subtype_score_util import get_cumulative_scores_between_dates
from main.util.breach_util import get_all_breaches_between_dates
from main.util.employee_util import get_breaches_for_period_using_dates, get_breach_data, get_employees_under_manager, update_breaches_for_inactive_employee, update_breaches_for_active_employee
from main.util.user_util import get_user_employee_readable_entities
from main.util.user_util import *
from main import logger


def view_text(path: Union[str, List[str]], blob_name, blob_label):
    return lambda view, context, model, name: ResumeView(model, path) \
        .markup(context, '', lambda d: f'<p>TEST MESSAGE {model.email_address}</p>')


class FilterByRecommendedAction(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            recommended_actions = db.session.query(DynamicRecommendedActions.recommended_action).distinct().all()
            recommended_action_list = [value[0] for value in recommended_actions]
            options = [(value, value) for value in recommended_action_list]
            return options


class FilterByEmail(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            emails = db.session.query(Employee.email_address).distinct().all()
            email_list = [value[0] for value in emails]
            options = [(value, value) for value in email_list]
            return options


class EmployeeListView(SecuredReferentialView):
    details_template = 'details_employee.html'
    # can_create = True
    can_edit = False
    can_view_details = True
    # can_delete = True
    page_size = 50
    can_export = True
    manager_view = False
    employee_columns = [Employee.breach_period,
                        Employee.email_address,
                        Employee.employee_name,
                        Employee.employee_igg,
                        Employee.job_title,
                        Employee.contract_type,
                        Employee.business_unit,
                        Employee.legal_entity,
                        Employee.location,
                        Employee.employee_status,
                        Employee.manager_email_address,
                        Employee.number_of_unique_breach_categories,
                        Employee.number_of_unique_breach_types,
                        Employee.total_breach_score,
                        Employee.cumulative_number_of_breaches,
                        Employee.recommended_action,
                        Employee.date_sent_to_disciplinary_committee
                        ]

    column_labels = {
        "breach_period": "Breach Period",
        "employee_name": "Employee Name",
        "business_unit": "BU/SU",
        "employee_status": "Employee Status",
        "number_of_unique_breach_categories": "Number of Unique Breach Categories",
        "number_of_unique_breach_types": "Number of Unique Breach Types",
        "total_breach_score": "12-Month Rolling Cumulative Breach Score",
        "cumulative_number_of_breaches": "Total Breaches in Last 12-Months",
        "recommended_action": "Recommended Action",
        "date_sent_to_disciplinary_committee": "Date Sent to Committee",
        "employee_igg": "Employee IGG"
    }

    column_descriptions = {
        "total_breach_score": "Cumulative Score of all breaches in the previous 12 months",
        "cumulative_number_of_breaches": "Count of all the breaches in the previous 12 months"
    }

    # Details and list
    column_list = employee_columns

    column_details_list = [  'email_address',
                              'employee_name',
                              'employee_igg',
                              'job_title',
                              'contract_type',
                              'physical_start_date',
                              'business_unit',
                              'legal_entity',
                              'location',
                              'manager_email_address',
                              'date_sent_to_disciplinary_committee',
                              'employee_status'
                          ]


    form_columns = ['date_sent_to_disciplinary_committee', 'employee_status']

    form_args = {
        'date_sent_to_disciplinary_committee' : {
            'description': 'Please enter the dates as YYYY-MM-DD'
        }
    }

    column_filters = [Employee.employee_name,
                      FilterByEmail(column=Employee.email_address, name='Email Address'),
                      Employee.business_unit,
                      Employee.employee_igg,
                      Employee.job_title,
                      Employee.contract_type,
                      Employee.legal_entity,
                      Employee.location,
                      Employee.manager_email_address,
                      FilterByRecommendedAction(Employee.recommended_action, 'Recommended Action'),
                      Employee.employee_status
                      ]


    def is_accessible(self):
        try:
            profile_name = get_user_profile_name()
            match profile_name:
                case 'Administrator':
                    self.can_edit = True
                    self.can_view_details = True
                    return True
                case 'Unit Breach Policy Officer (EMEA)':
                    self.can_edit = True
                    self.can_view_details = True
                    return True
                case 'Breach Case Inputter (EMEA)':
                    self.can_view_details = False
                    return False
                case 'Manager':
                    self.can_view_details = True
                    self.manager_view = True
                    return True
            return False
        except NoValidSGIAMProfileException as e:
            logger.error(e)
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/http401/custom-breachlog-view')

    def get_query(self):
        profile_name = get_user_profile_name()
        if profile_name == 'Administrator':
            return self.session.query(self.model)

        breach_readable_entities = get_user_breach_readable_entities()
        breach_readable_bpos = get_user_breach_readable_bpos()

        entities_filter = self.model.legal_entity.in_(breach_readable_entities)\

        match profile_name:
            case 'Unit Breach Policy Officer (EMEA)':
                filter_condition = or_(
                    and_(*[self.model.business_unit.like(f"{business_unit}/%") for business_unit in
                           breach_readable_bpos], entities_filter),
                )
                return self.session.query(self.model).filter(filter_condition)

        query = super(EmployeeListView, self).get_query()
        # query = query.filter(self.model.recommended_action.is_not(None))
        employee_readable_entities = get_user_employee_readable_entities()
        entities_filter = or_(not employee_readable_entities, self.model.legal_entity.in_(employee_readable_entities))
        if self.manager_view:
            query = query.filter(and_(or_(self.model.entity == null(), entities_filter), (self.model.email_address.in_(get_employees_under_manager(current_user.email)))))
        else:
            query = query.filter(or_(self.model.entity == null(), entities_filter))
        return query

    def get_count_query(self):
        query = super(EmployeeListView, self).get_count_query()
        query = query.filter(self.model.recommended_action.is_not(None))
        employee_readable_entities = get_user_employee_readable_entities()
        entities_filter = or_(not employee_readable_entities, self.model.entity.in_(employee_readable_entities))
        query = query.filter(or_(self.model.entity == null(), entities_filter))
        return query

    @staticmethod
    def get_sensitivity_level(cumulative_score):
        return True if int(cumulative_score) >= 9 else False

    @staticmethod
    def get_breach_year(date_obj):
        return date_obj.year + 1 if date_obj.month >= 10 else date_obj.year

    @staticmethod
    def get_cumulative_freq_for_a_period(email_address, start_date, end_date, valid_only=False):
        breaches = get_all_breaches_between_dates(email_address, start_date, end_date, valid_only=valid_only)
        return len(breaches)

    @staticmethod
    def get_recommended_action_for_a_period(score):
        if score >= 10:
            score = '>=10'
        if score == 0:
            return "No action"
        recommended_action = DynamicRecommendedActions.query.filter(
            DynamicRecommendedActions.total_breach_score == str(score)).first().recommended_action
        return recommended_action

    @expose('/details/', methods=('GET', 'POST'))
    def details_view(self):
        user_profile_name = get_user_profile_name()
        if user_profile_name != 'Administrator' and user_profile_name != 'Unit Breach Policy Officer (EMEA)':
            return self.inaccessible_callback('edit')
        self.is_accessible()
        if not self.can_view_details:
            return self.inaccessible_callback('edit')

        return_url = get_redirect_target() or self.get_url('.index_view')
        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)
        model = self.get_one(id)
        breach_data = get_breach_data(model.email_address)
        self._template_args['breach_data'] = breach_data
        self._template_args['id'] = id
        return super(EmployeeListView, self).details_view()

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
        # recalculate_recommended_action(db.session)
        return super().get_list(page, sort_column, sort_desc, search, filters,
                                execute, page_size)

    def on_form_prefill(self, form, id):
        presingles = get_all_singles()
        singles = {}
        # # # drop down box sort by values
        for key, value in presingles.items():
            if key == 'employee_status':
                singles['employee_status'] = sorted(value)

        def find_single(tuple):
            for key, choices in singles.items():
                if tuple[0] == key:
                    form_choices(form, key, False, tuple[1], [(v, v) for v in singles[key]])
                    return

        for tuple in form._unbound_fields:
            find_single(tuple)

        return form

    def on_model_change(self, form, model, is_created):
        if not is_created:
            if model.employee_status == 'Inactive':
                update_breaches_for_inactive_employee(model.email_address)
            elif model.employee_status == 'Active':
                update_breaches_for_active_employee(model.email_address)
