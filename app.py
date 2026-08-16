# 1- Initiate security
import os
import sys
import time

import jinja2
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from werkzeug.middleware.proxy_fix import ProxyFix

from cpla_flask_admin.util.file_parser import FileParser
from main import logger
from main.app_permissions import scopes_immutables
from main.util.breach_util import delete_expired_breaches

logger.info(scopes_immutables)

from cpla_flask_admin.util.vault import generate_properties_file

logger.info("Generate secret files ...")
generate_properties_file()

# 2- Imports
from main.views.model_employee import EmployeeListView
from main.schema.model_all import *
from cpla_flask_admin_files.app_files import create_app_with_files
from main.app_routes import app_routes
from main.schema.data_init import singles_init, remove_excess_roles
from main.views.model_breach import BreachDataView
from main.views.model_draft import DraftDataView
from main.views.model_batch_history import BatchHistoryDataView
from main.views.model_score import ScoreDataView
from main.views.model_breach_subtype_score import BreachSubtypeScoreDataView
from main.views.model_blacklisted_emails import BlacklistEmailDataView
from main.schema.model_all import BatchHistory, Score, BreachSubtypeScore
from main.system_extracts.email_night_batch import run_email_night_batch
from main.system_extracts.gems_breaches import run_gems_night_batch
from main.system_extracts.mandatory_leave import run_mandatory_leave_night_batch
from main.system_extracts.mandatory_training import run_mandatory_training_night_batch
from main.system_extracts.process_breach_excel import run_excel_parser
from main.util.azure_storage_blob import main_upload_blob_storage
from main.views.model_dynamic_recommended_actions import DynamicActionsDataView
from main.util.employee_util import recalculate_recommended_action_for_all_employees, update_expired_breaches, \
    refresh_breaches
from main.system_extracts.phishing import run_phishing_parser
from main.system_extracts.system_extracts_health_report import run_weekly_extract_history_email
from cpla_flask_admin.util.admin_view_secured import firewall_read, central_security
from cpla_flask_admin_files.schema_abstract.model_all import FileBlob
from flask import send_file
import io
import zlib
from flask_security import roles_accepted
import threading

from kubernetes import client, config, watch
from datetime import datetime, timedelta

# Load Kubernetes in-cluster configuration
if os.environ.get('webenv', '') != 'local':
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    POD_NAME = os.getenv("POD_NAME")
else:
    POD_NAME = 'local'


logger.info(f"ENV REPOSITORY: {os.environ.get('REPOSITORY')}")
logger.info(f"ENV webenv: {os.environ.get('webenv')}")



scheduler = BackgroundScheduler()

# Leadership lease duration (in seconds)
LEASE_DURATION_SECONDS = 60  # Leader must refresh within this time
CHECK_INTERVAL_SECONDS = 15  # How often to check/renew leadership

def get_namespace():
    namespace_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    try:
        with open(namespace_file_path, 'r') as f:
            namespace = f.read().strip()
            print(f"Namespace: {namespace}")
        return namespace
    except Exception as e:
        logger.error(f'Namespace not found: {e}')
        return None


def is_pod_alive(pod_name, namespace):
    """Check if a pod is still running."""
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
        phase = pod.status.phase
        return phase in ['Running', 'Pending']
    except Exception as e:
        logger.warning(f"Pod {pod_name} not found or error: {e}")
        return False

def is_lease_expired(lease_timestamp):
    """Check if the leadership lease has expired."""
    if not lease_timestamp:
        return True
    try:
        lease_time = datetime.fromisoformat(lease_timestamp)
        expiration_time = lease_time + timedelta(seconds=LEASE_DURATION_SECONDS)
        is_expired = datetime.now() > expiration_time
        if is_expired:
            logger.info(f"Lease expired. Last update: {lease_timestamp}, Expiration: {expiration_time}")
        return is_expired
    except Exception as e:
        logger.error(f"Error parsing lease timestamp: {e}")
        return True


def claim_leadership():
    """Try to become the leader with lease-based expiration."""
    if os.environ.get('webenv', '') not in ['prod', 'prd']:
        return True

    namespace = get_namespace()
    if not namespace:
        return False

    try:
        configmap_name = f"{os.environ.get('REPOSITORY')}-leader"
        config_map = v1.read_namespaced_config_map(configmap_name, namespace)

        current_leader = config_map.data.get("leader", "")
        lease_timestamp = config_map.data.get("lease_timestamp", "")

        logger.info(f"Current leader: {current_leader}, Lease: {lease_timestamp}")

        # Check if we should try to claim leadership
        should_claim = False

        if not current_leader:
            logger.info("No current leader, claiming leadership")
            should_claim = True
        elif current_leader == POD_NAME:
            # We are already the leader, just renew the lease
            logger.info(f"Renewing lease for {POD_NAME}")
            should_claim = True
        elif is_lease_expired(lease_timestamp):
            logger.info(f"Lease expired for {current_leader}, attempting to claim leadership")
            should_claim = True
        elif not is_pod_alive(current_leader, namespace):
            logger.info(f"Current leader {current_leader} is not alive, attempting to claim leadership")
            should_claim = True
        else:
            logger.info(f"Leader {current_leader} is active with valid lease")
            return False

        if should_claim:
            # Update ConfigMap with this pod as leader and current timestamp
            now = datetime.now().isoformat()
            v1.patch_namespaced_config_map(
                name=configmap_name,
                namespace=namespace,
                body={"data": {"leader": POD_NAME, "lease_timestamp": now}},
            )
            logger.info(f"Leadership claimed by {POD_NAME} at {now}")
            print(f"Leadership claimed by {POD_NAME} at {now}")
            return True

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"ConfigMap {configmap_name} not found. Please create it first.")
        else:
            logger.error(f"Kubernetes API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error in claim_leadership: {e}")
        return False

    return False


def job_listener(event):
    if event.exception:
        print(f"Job crashed: {event.job_id} - {event.exception}")
    else:
        print(f"Job executed successfully: {event.job_id}")

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
def start_scheduler():
    if not scheduler.running:
        if 'db' not in sys.argv:
            scheduler.start()
            logger.info("Scheduler Started")
            print("Scheduler Started")

# Stop the scheduler if running
def stop_scheduler():
    if scheduler.running:
        print("Stopping scheduler...")
        scheduler.shutdown(wait=False)

# Watcher function for leader updates
def monitor_leadership():
    is_leader = False  # Tracks if this pod is currently the leader

    while True:
        try:
            logger.info('Monitoring leadership')

            # Check if this pod can claim leadership
            is_leader_now = claim_leadership()

            if is_leader_now and not is_leader:
                # This pod becomes the leader
                is_leader = True
                logger.info(f'Pod {POD_NAME} became the leader')
                start_scheduler()
            elif not is_leader_now and is_leader:
                # This pod loses leadership
                is_leader = False
                logger.warning(f'Pod {POD_NAME} lost leadership')
                stop_scheduler()
            elif is_leader_now and is_leader:
                # Still the leader, lease was renewed
                logger.info(f'Pod {POD_NAME} renewed leadership lease')

        except Exception as e:
            logger.error(f"Error in monitor_leadership: {e}")
            # On error, assume we lost leadership to be safe
            if is_leader:
                is_leader = False
                stop_scheduler()

        time.sleep(CHECK_INTERVAL_SECONDS)

def app_init():
    remove_excess_roles()
    singles_init()


# 3- Start Application
new_app = create_app_with_files(
    'policy-breach-register', 'Policy Breach Register', '/breach',
    app_routes,
    [
        lambda s: BreachDataView(Breach, s, name="Breach Log"),
        lambda s: DraftDataView(BreachDrafts, s, name="My Drafts"),
        lambda s: EmployeeListView(Employee, s, name='Employee List'),
        lambda s: BatchHistoryDataView(BatchHistory, s, name="Extract History"),
        lambda s: ScoreDataView(Score, s, name="Breach Scores Table"),
        lambda s: BreachSubtypeScoreDataView(BreachSubtypeScore, s, name="Breach Sub-Questions Table"),
        lambda s: BlacklistEmailDataView(DoNotSendEmailTo, s, name="Email Blacklist"),
        lambda s: DynamicActionsDataView(DynamicRecommendedActions, s, name="Recommended Actions Table")
    ],
    None,
    app_init,
    lambda zip_id, entity, file_name, binary, extra_args:
    FileParser(db).depose_file_or_email(entity, file_name, binary, zip_id, extra_args),
    lambda zip_id: None,
)

# scheduler.add_job(func=main_upload_blob_storage, trigger="cron", minute='0,30')
scheduler.add_job(func=run_email_night_batch, kwargs={'app_context': new_app.app_context()}, trigger="cron", hour=0, minute=15)
# scheduler.add_job(func=run_mandatory_training_night_batch, kwargs={'app_context': new_app.app_context()}, trigger="cron", hour=0, minute=30)
# scheduler.add_job(func=run_mandatory_leave_night_batch, kwargs={'app_context': new_app.app_context()}, trigger="cron", hour=1, minute=45)
# scheduler.add_job(func=run_phishing_parser, kwargs={'app_context': new_app.app_context()}, trigger="interval", minutes=59)
# scheduler.add_job(func=run_gems_night_batch, kwargs={'app_context': new_app.app_context()}, trigger="cron", hour=4, minute=30)
# scheduler.add_job(func=run_mandatory_training_night_batch, kwargs={'app_context': new_app.app_context(), 'country': 'CHINA'}, trigger="cron", hour=5, minute=30)
# scheduler.add_job(func=run_gems_night_batch, kwargs={'app_context': new_app.app_context(), 'country': 'CHINA'}, trigger="cron", hour=6, minute=30)
# scheduler.add_job(func=run_excel_parser, kwargs={'db_session': db.session, 'app_context': new_app.app_context()}, trigger="interval", minutes=20)
# scheduler.add_job(func=recalculate_recommended_action_for_all_employees, kwargs={'app_context': new_app.app_context()}, trigger="cron", hour=1, minute=0)
# scheduler.add_job(func=run_weekly_extract_history_email, kwargs={'db_session': db.session, 'app_context': new_app.app_context()}, trigger="cron", day_of_week='mon', hour=9, minute=0)
scheduler.add_job(func=update_expired_breaches, kwargs={'db_sess': db.session, 'app_context': new_app.app_context()}, trigger="cron", hour=2, minute=0)
scheduler.add_job(func=refresh_breaches, kwargs={'db_sess': db.session, 'app_context': new_app.app_context()}, trigger="cron", hour=3, minute=30)
scheduler.add_job(func=delete_expired_breaches, kwargs={'db_sess': db.session, 'app_context': new_app.app_context()}, trigger="cron", hour=3, minute=0)

leadership_thread = threading.Thread(target=monitor_leadership, daemon=True)
leadership_thread.start()

new_app.jinja_env.add_extension('jinja2.ext.do')

# loads in custom template html files for Breach Log under cpla-policy-breach-register/src/main/template
if os.environ.get('webenv', '') == 'local':
    new_app.jinja_loader = jinja2.ChoiceLoader([new_app.jinja_loader, jinja2.FileSystemLoader('templates')])
else:
    new_app.jinja_loader = jinja2.ChoiceLoader([new_app.jinja_loader, jinja2.FileSystemLoader('./main/templates')])

if __name__ == '__main__':
    new_app.wsgi_app = ProxyFix(
        new_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )
    new_app.run(debug=True, host=new_app.config['APP_HOST'], port=new_app.config['APP_PORT'])
