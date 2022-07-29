from airflow.configuration import conf
from debussy_concert.reverse_etl.composition.clair_de_lune import ClairDeLune
from debussy_concert.reverse_etl.config.reverse_etl import ConfigReverseEtl
from debussy_concert.core.service.workflow.airflow import AirflowService
from debussy_concert.core.service.injection import inject_dependencies

dags_folder = conf.get('core', 'dags_folder')
env_file = f'{dags_folder}/examples/reverse_etl_participant/environment.yaml'
composition_file = f'{dags_folder}/examples/reverse_etl_participant/composition.yaml'

reverse_etl_config = ConfigReverseEtl.load_from_file(
    composition_config_file_path=composition_file,
    env_file_path=env_file
)
airflow_service = AirflowService()
inject_dependencies(workflow_service=airflow_service, config_composition=reverse_etl_config)

composition = ClairDeLune()
reverse_etl_movement_fn = composition.bigquery_to_storage_reverse_etl_to_rdbms_movement_builder
dag = composition.play(reverse_etl_movement_fn)
