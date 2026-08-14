from typing import List
from typing import Union

from flask_security import current_user
from werkzeug.utils import redirect
from wtforms import SelectMultipleField

from cpla_flask_admin.util.admin_view_secured import SecuredDataView, form_choices, SecuredReferentialView
from cpla_flask_admin.util.category_theory import get_all_singles
from cpla_flask_admin.util.custom_exceptions import NoValidSGIAMProfileException
from cpla_flask_admin.util.wtform_view_resume import view_object_as_string, view_date, view_people, ResumeView
from cpla_flask_admin.util.wtform_zmisc_fp import fields
from cpla_flask_admin.util.wtform_zmisc_text import get_text
from main import logger
from main.schema.model_all import Score, BreachProcess
from main.util.accessList import AccessList
from main.util.custom_exceptions import DuplicateBreachTypeException
from main.util.email_template_util import get_all_email_template_names
from main.util.score_util import is_breach_present
from main.util.breach_process_util import get_all_breach_process_ids
from main.util.user_util import get_user_profile_name


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


class ScoreDataView(SecuredReferentialView):
    can_create = False
    can_edit = False
    can_view_details = True
    can_delete = False
    page_size = 50
    can_export = True

    score_case_columns = [Score.policy, Score.transversal_breach, Score.breach_type, Score.score, Score.breach_type_group,
                          Score.hide_from_case_view, Score.email_template, Score.additional_recipients, Score.breach_process_id, Score.freeze_count]

    column_labels = {"transversal_breach":"Specific/Transversal Breach", "policy": "Breach Category", "breach_type": "Breach Type",
                     "breach_type_group": "Breach Type Group",
                     "score": "Score", "hide_from_case_view": "Hide From Case View",
                     "freeze_count": "Freeze Count",
                     "email_template": "Email Template Used",
                     "additional_recipients": "Additional Recipients",
                     "breach_process_id": "Breach Process Owner ID"}

    column_descriptions = {
        "hide_from_case_view": "To restrict certain breach types from user selection, e.g., for breach type generated from System Extracts",
        "breach_type_group": "Group name used to cluster certain Breach Types to calculate Breach Frequency",
        "create_time": "Creation Time in CET",
        "last_update_time": "Last Update Time in CET",
        "freeze_count": "Enabling this will freeze the scoring beyond this frequency but count will be preserved",
        "additional_recipients": "CC emails to additional recipients ( , separated)"
    }

    # Details and list
    column_list = [Score.transversal_breach, Score.policy, Score.breach_type, Score.score, Score.email_template, Score.additional_recipients, Score.breach_process_id,
                   Score.breach_type_group,
                   Score.hide_from_case_view, Score.freeze_count] + [Score.create_by, Score.create_time,
                                                 Score.last_update_by, Score.last_update_time]

    column_details_list = [Score.transversal_breach, Score.policy, Score.breach_type, Score.score, Score.email_template, Score.additional_recipients, Score.breach_process_id,
                           Score.hide_from_case_view, Score.freeze_count] + [Score.create_by, Score.create_time, Score.last_update_by,
                                                         Score.last_update_time]

    column_filters = [Score.transversal_breach, Score.policy, Score.breach_type, Score.score,
                      Score.hide_from_case_view, Score.freeze_count] + [Score.create_by, Score.create_time,
                                                    Score.last_update_by, Score.last_update_time]

    ## Form (Edit + Create)
    form_columns = score_case_columns.copy()

    # Export everything
    column_export_list = column_details_list
    column_formatters_export = dict([fields(view_export_text, 'action') + fields(view_export_text, 'description')])
    column_formatters = dict(
        fields(view_people, 'created_by', 'updated_by') +
        fields((view_date, '%Y-%m-%d %H:%M:%S %p'), "create_time", "last_update_time") +
        fields((view_object_as_string, 100), 'breach_type'),
        **{'hide_from_case_view': lambda view, context, model, name: 'Yes' if model.hide_from_case_view else 'No'}
    )

    def is_accessible(self):
        try:
            profile_name = get_user_profile_name()
            match profile_name:
                case 'Administrator':
                    self.can_create = True
                    self.can_edit = True
                    self.can_view_details = True
                    self.can_delete = True
                    return True
                case 'Unit Breach Policy Officer (EMEA)':
                    self.can_view_details = True
                    return True
            return False
        except NoValidSGIAMProfileException as e:
            logger.error(e)
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/http401/custom-breachlog-view')

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.create_by = str(current_user.igg)
            model.last_update_by = str(current_user)

            # If breach_type already exists throw an exception which will rollback the DB transaction preventing duplication.
            if is_breach_present(model.breach_type, model.policy, model.transversal_breach):
                raise DuplicateBreachTypeException(breach_type=model.breach_type, breach_category=model.policy)
        else:
            model.last_update_by = str(current_user)

        super(ScoreDataView, self).on_model_change(form, model, is_created)

    def scaffold_form(self):
        form = super(ScoreDataView, self).scaffold_form()
        form.breach_process_id = SelectMultipleField(validate_choice=False)
        return form

    def on_form_prefill(self, form, id):
        form.hide_from_case_view.render_kw = {'style': 'width: auto;'}
        form.policy.render_kw = {'readonly': True}
        form.breach_type.render_kw = {'readonly': True}

        presingles = get_all_singles()
        singles = {}
        # Key-Value Pairs for breach_type and breach_category(stored as 'policy' in single table) inside singles dict
        for key, value in presingles.items():
            if key == 'breach_type':
                singles[key] = sorted(value, reverse=True)
            elif key == 'policy':
                singles[key] = sorted(value, reverse=True)
            elif key == 'breach_type_group':
                singles[key] = sorted(value, reverse=True)
            elif key == 'transversal_breach':
                singles[key] = sorted(value, reverse=True)

        # To get all templates from the email_template table
        singles['email_template'] = get_all_email_template_names()
        singles['breach_process_id'] = get_all_breach_process_ids().keys()

        def find_single(tuple):
            # Drop down boxes for breach_type and breach_category from singles dict
            for key, choices in singles.items():
                if tuple[0] == key:
                    # In update mode, freeze the breach_type as it cannot be edited. Rest of the fields can be modified.
                    if key == 'breach_process_id':
                        form_choices(form, key, True, tuple[1], [(v, v) for v in singles[key]])
                    else:
                        form_choices(form, key, False, tuple[1], [(v, v) for v in singles[key]])
                    return

        for tuple in form._unbound_fields:
            find_single(tuple)

        if id:
            breach_process_id = Score.query.filter(Score.id == id).with_entities(Score.breach_process_id).scalar()
            form.breach_process_id.data = breach_process_id

        return form
