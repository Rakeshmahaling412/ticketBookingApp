from main.schema.model_all import EmailTemplate
from cpla_flask_admin.schema.admin import db


def get_email_template_by_name(template_name: str):
    query = db.session.query(EmailTemplate.email_template_content).filter(EmailTemplate.email_template_name == template_name)
    return query.scalar()


def get_all_email_template_names():
    query_result = db.session.query(EmailTemplate.email_template_name).all()
    template_names = [template_tuple[0] for template_tuple in query_result]
    return template_names
