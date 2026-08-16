from typing import List
from typing import Union
from werkzeug.utils import redirect

from main import logger
from flask import request, has_app_context
from cpla_flask_admin.util.admin_view_secured import SecuredReferentialView
from cpla_flask_admin.util.wtform_view_resume import ResumeView
from cpla_flask_admin.util.wtform_zmisc_fp import fields
from cpla_flask_admin.util.wtform_zmisc_text import get_text
from main.schema.model_all import DoNotSendEmailTo
from flask_admin.contrib.sqla.filters import BaseSQLAFilter
from main.util.user_util import *
from cpla_flask_admin.schema.admin import db


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



class FilterByEmail(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(self.column == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        if has_app_context():
            emails = db.session.query(DoNotSendEmailTo.email).distinct().all()
            email_list = [value[0] for value in emails]
            options = [(value, value) for value in email_list]
            return options


class BlacklistEmailDataView(SecuredReferentialView):
    def is_accessible(self):
        try:
            profile_name = get_user_profile_name()
            if profile_name in ['Administrator']:
                self.can_delete = True
                self.can_create = True
                self.can_edit = True
                return True
            return False
        except NoValidSGIAMProfileException as e:
            logger.error(e)
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/http401/custom-breachlog-view')

    score_case_columns = [DoNotSendEmailTo.email]

    column_labels = {"email": "Email"}

    column_descriptions = {
        "email": "Email of user to be blacklisted"
    }

    # Details and list
    column_list = score_case_columns

    column_details_list = score_case_columns

    column_filters = [FilterByEmail(column=DoNotSendEmailTo.email, name='Email Address')]

    ## Form (Edit + Create)
    form_columns = score_case_columns.copy()

    # Export everything
    column_export_list = column_details_list
    column_formatters_export = dict([fields(view_export_text, 'action') + fields(view_export_text, 'description')])
