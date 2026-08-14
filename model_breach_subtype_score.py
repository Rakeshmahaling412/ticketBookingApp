from werkzeug.utils import redirect
from wtforms.validators import DataRequired

from cpla_flask_admin.util.admin_view_secured import SecuredDataView, extract_entities, SecuredReferentialView
from cpla_flask_admin.util.custom_exceptions import NoValidSGIAMProfileException
from main import logger
from main.schema.model_all import BreachSubtypeScore
from cpla_flask_admin.util.wtform_zmisc_fp import fields, field
from cpla_flask_admin.util.wtform_view_resume import view_object_as_string, view_date, view_people, view_html, \
    ResumeView
from cpla_flask_admin.util.wtform_category_form import CategoryField
from cpla_flask_admin.util.wtform_zmisc_text import get_text
from main.util.accessList import AccessList
from flask_security import current_user
from cpla_flask_admin.util.admin_view_secured import form_choices, get_all_singles, form_trees_refresh
from flask_admin.form import rules
from wtforms import RadioField
from typing import Union
from typing import List
from main.util.custom_exceptions import *
from main.util.breach_subtype_score_util import breach_subtype_present_for_breach_type_group, breach_subtype_group_present_for_question, frequency_present_for_breach_type_group, question_different_for_breach_type_group_and_level
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


def validate_model(model):
    # Validations
    if not model.breach_subtype or len(model.breach_subtype.strip()) == 0:
        raise EmptyBreachSubTypeException()
    if model.level <= 0:
        raise InvalidLevelException()

    if (model.frequency_count is None) and (None in [model.question, model.level]):
        raise NullQuestionOrLevelException()
    else:
        if model.frequency_count != None:
            if model.question:
                raise InvalidArgumentsForBreachSubtypeScore()
            if model.frequency_count < 2:
                raise WrongFrequencyCountException()
            if breach_subtype_present_for_breach_type_group(breach_type_group=model.breach_type_group,
                                                            breach_subtype=model.breach_subtype):
                raise DuplicateBreachSubTypeException(breach_type_group=model.breach_type_group,
                                                      breach_subtype=model.breach_subtype)
            if frequency_present_for_breach_type_group(breach_type_group=model.breach_type_group,
                                                       frequency=model.frequency_count):
                raise DuplicateBreachTypeGroupFrequencyException(breach_type_group=model.breach_type_group,
                                                                 frequency=model.frequency_count)
        else:
            if model.frequency_count:
                raise InvalidArgumentsForBreachSubtypeScore()
            if breach_subtype_group_present_for_question(breach_type_group=model.breach_type_group,
                                                         breach_subtype=model.breach_subtype,
                                                         question=model.question):
                raise DuplicateBreachTypeGroupQuestionException(breach_type_group=model.breach_type_group,
                                                                breach_subtype=model.breach_subtype,
                                                                question=model.question)
            if question_different_for_breach_type_group_and_level(breach_type_group=model.breach_type_group,
                                                                  level=model.level):
                raise MultipleQuestionForOneLevelException()


class BreachSubtypeScoreDataView(SecuredReferentialView):
    can_create = False
    can_edit = False
    can_view_details = True
    can_delete = False
    page_size = 50
    can_export = True

    score_case_columns = [BreachSubtypeScore.breach_subtype, BreachSubtypeScore.breach_type_group, BreachSubtypeScore.score, BreachSubtypeScore.frequency_count, BreachSubtypeScore.question,
                          BreachSubtypeScore.level, BreachSubtypeScore.hide_from_case_view]

    column_labels = {"breach_subtype": "Breach Type", "policy": "Breach Category", "breach_types": "Breach Types", "frequency_count": "Count of the Breach SubType",
                     "score": "Incremental Score", "hide_from_case_view": "Hide From Case View", "question": "Sub-Question"}

    column_descriptions = {
        "question": "Sub-question to prompt if the Breach Type is a sub-question option",
        "breach_type_group": "Group name used to cluster certain Breach Types to calculate Breach Frequency",
        "score": "Score to add to the base score of the parent Breach Type",
        "frequency_count": "Number to define the frequency a breach sub-type represents (apply only to frequency count)",
        "hide_from_case_view": "To restrict certain breach types from user selection, e.g., for breach types generated from System Extracts"
    }

    # Details and list
    column_list = [BreachSubtypeScore.question, BreachSubtypeScore.breach_subtype, BreachSubtypeScore.breach_type_group, BreachSubtypeScore.score, BreachSubtypeScore.frequency_count,
                                BreachSubtypeScore.hide_from_case_view]

    column_details_list = [BreachSubtypeScore.question, BreachSubtypeScore.breach_subtype, BreachSubtypeScore.breach_type_group, BreachSubtypeScore.score, BreachSubtypeScore.frequency_count,
                                        BreachSubtypeScore.hide_from_case_view]

    column_filters = [BreachSubtypeScore.question, BreachSubtypeScore.breach_subtype, BreachSubtypeScore.breach_type_group, BreachSubtypeScore.frequency_count, BreachSubtypeScore.score, BreachSubtypeScore.hide_from_case_view]

    ## Form (Edit + Create)
    form_columns = score_case_columns.copy()

    # Export everything
    column_export_list = column_details_list
    column_formatters_export = dict([fields(view_export_text, 'action') + fields(view_export_text, 'description')])
    column_formatters = dict(
        fields(view_people, 'created_by', 'updated_by') +
        fields((view_date, '%Y-%m-%d'), "create_time", "last_update_time"),
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
        else:
            model.last_update_by = str(current_user)

        validate_model(model)

        super(SecuredReferentialView, self).on_model_change(form, model, is_created)

    def on_form_prefill(self, form, id):
        presingles = get_all_singles()
        singles = {}
        # # # drop down box sort by values
        for key, value in presingles.items():
            if key == 'breach_type_group':
                singles[key] = sorted(value, reverse=True)

        def find_single(tuple):
            for key, choices in singles.items():
                if tuple[0] == key:
                    form_choices(form, key, False, tuple[1], [(v, v) for v in singles[key]])
                return

        for tuple in form._unbound_fields:
            find_single(tuple)

        # To left align the checkbox for hide_from_case_view
        form.hide_from_case_view.render_kw = {'style': 'width: auto;'}
        return form
