from datetime import timedelta
import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.sensors.filesystem import FileSensor
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_HOME = "/home/sandeep/social-media-etl"
JSON_FILE = f"{PROJECT_HOME}/data/incoming/social_media_posts.json"
MEDIA_DIR = f"{PROJECT_HOME}/data/media"
PYTHON = "/home/sandeep/airflow-env/bin/python3"
SCRIPT = f"{PROJECT_HOME}/scripts/transform_posts.py"

with DAG(
    dag_id="social_media_etl",
    description="Ingest social media data into HDFS and load transformed posts into SQLite",
    start_date=pendulum.datetime(2026, 9, 30, tz="Asia/Kolkata"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["social-media", "etl", "hdfs", "sqlite"],
) as dag:

    wait_for_json = FileSensor(
        task_id="wait_for_json_file",
        filepath=JSON_FILE,
        fs_conn_id="fs_default",
        poke_interval=30,
        timeout=1800,
        mode="reschedule",
    )

    ingest_to_hdfs = BashOperator(
        task_id="ingest_json_and_images_to_hdfs",
        bash_command=f"""
set -e
hdfs dfs -mkdir -p /social-media/raw/json /social-media/raw/media
hdfs dfs -put -f {JSON_FILE} /social-media/raw/json/
hdfs dfs -put -f {MEDIA_DIR}/*.jpg /social-media/raw/media/
echo "JSON and images successfully ingested into HDFS"
""",
        execution_timeout=timedelta(minutes=10),
    )

    transform_and_load = BashOperator(
        task_id="transform_and_load_sqlite",
        bash_command=f"{PYTHON} {SCRIPT}",
        execution_timeout=timedelta(minutes=10),
    )

    wait_for_json >> ingest_to_hdfs >> transform_and_load
