# Social Media ETL Pipeline

An end-to-end ETL pipeline using Python, Apache Airflow, Hadoop HDFS, and SQLite.

## Workflow
1. Airflow FileSensor waits for the input JSON file.
2. Raw JSON and media files are ingested into HDFS.
3. Python validates and transforms social media posts.
4. Engagement metrics are calculated.
5. Transformed records are loaded into SQLite.

## Technologies
- Python
- Apache Airflow 3
- Hadoop HDFS
- SQLite
- Ubuntu / WSL

## Project Structure
- dags/ - Airflow DAG
- scripts/ - Python transformation script
- data/incoming/ - Sample JSON input
- data/media/ - Sample post images
- database/ - SQLite output (not tracked in Git)

## Run
The pipeline is orchestrated using the Airflow DAG
`social_media_etl`.

## Author
Sandeep Vishwakarma
