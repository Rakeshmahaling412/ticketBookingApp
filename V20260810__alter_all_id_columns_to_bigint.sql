-- Fix: all id columns were created as serial (integer) in the Python-era schema.
-- Java JPA entities map ids as Long (bigint). Alter all affected tables and their sequences.

ALTER TABLE batch_history                ALTER COLUMN id TYPE bigint;
ALTER TABLE breach                       ALTER COLUMN id TYPE bigint;
ALTER TABLE breach_subtype_score         ALTER COLUMN id TYPE bigint;
ALTER TABLE country_mapping              ALTER COLUMN id TYPE bigint;
ALTER TABLE deleted_breaches             ALTER COLUMN id TYPE bigint;
ALTER TABLE do_not_send_email_to         ALTER COLUMN id TYPE bigint;
ALTER TABLE dynamic_recommended_actions  ALTER COLUMN id TYPE bigint;
ALTER TABLE email                        ALTER COLUMN id TYPE bigint;
ALTER TABLE email_history                ALTER COLUMN id TYPE bigint;
ALTER TABLE email_template               ALTER COLUMN id TYPE bigint;
ALTER TABLE employee                     ALTER COLUMN id TYPE bigint;
ALTER TABLE error_log                    ALTER COLUMN id TYPE bigint;
ALTER TABLE file                         ALTER COLUMN id TYPE bigint;
ALTER TABLE file_blob                    ALTER COLUMN id TYPE bigint;
ALTER TABLE image                        ALTER COLUMN id TYPE bigint;
ALTER TABLE image_blob                   ALTER COLUMN id TYPE bigint;
ALTER TABLE legalentity_company_mapping  ALTER COLUMN id TYPE bigint;
ALTER TABLE profile                      ALTER COLUMN id TYPE bigint;
ALTER TABLE role                         ALTER COLUMN id TYPE bigint;
ALTER TABLE score                        ALTER COLUMN id TYPE bigint;
ALTER TABLE "user"                       ALTER COLUMN id TYPE bigint;
ALTER TABLE user_log                     ALTER COLUMN id TYPE bigint;

ALTER SEQUENCE batch_history_id_seq               AS bigint;
ALTER SEQUENCE breach_id_seq                      AS bigint;
ALTER SEQUENCE breach_subtype_score_id_seq        AS bigint;
ALTER SEQUENCE country_mapping_id_seq             AS bigint;
ALTER SEQUENCE deleted_breaches_id_seq            AS bigint;
ALTER SEQUENCE do_not_send_email_to_id_seq        AS bigint;
ALTER SEQUENCE dynamic_recommended_actions_id_seq AS bigint;
ALTER SEQUENCE email_id_seq                       AS bigint;
ALTER SEQUENCE email_history_id_seq               AS bigint;
ALTER SEQUENCE email_template_id_seq              AS bigint;
ALTER SEQUENCE employee_id_seq                    AS bigint;
ALTER SEQUENCE error_log_id_seq                   AS bigint;
ALTER SEQUENCE file_id_seq                        AS bigint;
ALTER SEQUENCE file_blob_id_seq                   AS bigint;
ALTER SEQUENCE image_id_seq                       AS bigint;
ALTER SEQUENCE image_blob_id_seq                  AS bigint;
ALTER SEQUENCE legalentity_company_mapping_id_seq AS bigint;
ALTER SEQUENCE profile_id_seq                     AS bigint;
ALTER SEQUENCE role_id_seq                        AS bigint;
ALTER SEQUENCE score_id_seq                       AS bigint;
ALTER SEQUENCE user_id_seq                        AS bigint;
ALTER SEQUENCE user_log_id_seq                    AS bigint;
