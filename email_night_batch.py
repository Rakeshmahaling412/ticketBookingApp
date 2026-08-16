import os

from main import logger
from main.util.email_util import generate_email_using_breach_email_content, get_breach_ids_to_send_email, send_email, \
            update_email_sent_status


def run_email_night_batch(app_context):
    try:
        with app_context:
            breach_ids = get_breach_ids_to_send_email()
            affected_breach_ids = []

            for breach_id in breach_ids:
                msg = generate_email_using_breach_email_content(breach_id)
                send_email(msg)
                affected_breach_ids.append(update_email_sent_status(breach_id, msg))
            logger.info('Sent email for Breach IDs: ', affected_breach_ids)
            return f'Sent email for Breach IDs: {affected_breach_ids}'
    except Exception as e:
        logger.error("Exception while sending email: ", str(e))
        return "exception " + str(e)






