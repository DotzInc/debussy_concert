from debussy_concert.core.phrase.utils.end import EndPhrase
from debussy_concert.core.phrase.utils.start import StartPhrase
from debussy_concert.core.composition.composition_base import CompositionBase
from debussy_concert.core.motif.mixins.bigquery_job import BigQueryTimePartitioning

from debussy_concert.reverse_etl.config.reverse_etl import ConfigReverseEtl
from debussy_concert.reverse_etl.config.movement_parameters.reverse_etl import CsvFile, ReverseEtlMovementParameters
from debussy_concert.reverse_etl.movement.reverse_etl import ReverseEtlMovement
from debussy_concert.reverse_etl.phrase.dw_to_reverse_etl import DataWarehouseToReverseEtlPhrase
from debussy_concert.reverse_etl.phrase.reverse_etl_to_storage import DataWarehouseReverseEtlToTempToStoragePhrase
from debussy_concert.reverse_etl.phrase.storage_to_destination import StorageToDestinationPhrase
from debussy_concert.reverse_etl.motif.storage_to_rdbms_motif import StorageToRdbmsQueryMotif
from debussy_concert.reverse_etl.motif.bigquery_query_job import BigQueryQueryJobMotif
from debussy_concert.reverse_etl.motif.bigquery_extract_job import BigQueryExtractJobMotif

from debussy_framework.v3.hooks.storage_hook import GCSHook
from debussy_framework.v3.hooks.db_api_hook import MySqlConnectorHook


class ClairDeLune(CompositionBase):
    config: ConfigReverseEtl

    def bigquery_to_storage_reverse_etl_to_rdbms_movement_builder(
        self,
        movement_parameters: ReverseEtlMovementParameters
    ):
        return self.reverse_etl_movement_builder(
            movement_parameters=movement_parameters
        )

    def reverse_etl_movement_builder(
        self,
        movement_parameters: ReverseEtlMovementParameters
    ) -> ReverseEtlMovement:
        start_phrase = StartPhrase()
        end_phrase = EndPhrase()
        csv_output_config: CsvFile = movement_parameters.output_config

        data_warehouse_raw_to_reverse_etl_phrase = self.data_warehouse_raw_to_reverse_etl_phrase(
            partition_type=movement_parameters.reverse_etl_dataset_partition_type,
            partition_field=movement_parameters.reverse_etl_dataset_partition_field,
            gcp_conn_id=self.config.environment.data_lakehouse_connection_id
        )

        data_warehouse_reverse_etl_to_storage_phrase = self.data_warehouse_reverse_etl_to_storage_phrase(
            destination_config=csv_output_config,
            gcp_conn_id=self.config.environment.data_lakehouse_connection_id
        )

        data_storage_to_rdbms_phrase = self.data_storage_to_rdbms_phrase(
            movement_parameters
        )

        name = f'ReverseEtlMovement_{movement_parameters.name}'

        movement = ReverseEtlMovement(
            name=name,
            start_phrase=start_phrase,
            data_warehouse_to_reverse_etl_phrase=data_warehouse_raw_to_reverse_etl_phrase,
            data_warehouse_reverse_etl_to_storage_phrase=data_warehouse_reverse_etl_to_storage_phrase,
            storage_to_destination_phrase=data_storage_to_rdbms_phrase,
            end_phrase=end_phrase
        )
        movement.setup(movement_parameters)
        return movement

    def data_warehouse_raw_to_reverse_etl_phrase(self, partition_type, partition_field, gcp_conn_id):
        time_partitioning = BigQueryTimePartitioning(type=partition_type, field=partition_field)

        bigquery_job = BigQueryQueryJobMotif(name='bq_to_reverse_etl_motif',
                                             write_disposition="WRITE_APPEND",
                                             create_disposition="CREATE_IF_NEEDED",
                                             time_partitioning=time_partitioning,
                                             gcp_conn_id=gcp_conn_id)

        phrase = DataWarehouseToReverseEtlPhrase(dw_to_reverse_etl_motif=bigquery_job)
        return phrase

    def data_warehouse_reverse_etl_to_storage_phrase(self, destination_config: CsvFile, gcp_conn_id):
        bigquery_job = BigQueryQueryJobMotif(name='bq_reverse_etl_to_temp_table_motif',
                                             write_disposition="WRITE_TRUNCATE",
                                             create_disposition="CREATE_IF_NEEDED",
                                             gcp_conn_id=gcp_conn_id)

        export_bigquery = BigQueryExtractJobMotif(name='bq_export_table_to_gcs_motif',
                                                  destination_format=destination_config.format,
                                                  field_delimiter=destination_config.field_delimiter,
                                                  gcp_conn_id=gcp_conn_id)

        phrase = DataWarehouseReverseEtlToTempToStoragePhrase(
            name='DataWarehouseReverseEtlToTempToStoragePhrase',
            datawarehouse_reverse_etl_to_temp_table_motif=bigquery_job,
            export_temp_table_to_storage_motif=export_bigquery
        )
        return phrase

    def data_storage_to_rdbms_phrase(self, movement_parameters: ReverseEtlMovementParameters):
        dest_conn_id = movement_parameters.destination_connection_id
        data_lakehouse_connection_id = self.config.environment.data_lakehouse_connection_id

        dbapi_hook = MySqlConnectorHook(rdbms_conn_id=dest_conn_id)
        storage_hook = GCSHook(gcp_conn_id=data_lakehouse_connection_id)
        storage_to_rdbms_destination = StorageToRdbmsQueryMotif(
            name='file_storage_to_build_insert_query_to_rdbms_motif',
            dbapi_hook=dbapi_hook,
            storage_hook=storage_hook,
            destination_table=movement_parameters.destination_uri
        )

        phrase = StorageToDestinationPhrase(name='StorageToRdbmsDestinationPhrase',
                                                 storage_to_destination_motif=storage_to_rdbms_destination)
        return phrase

    @classmethod
    def create_from_yaml(cls, environment_config_yaml_filepath, composition_config_yaml_filepath):
        config = ConfigReverseEtl.load_from_file(
            composition_config_file_path=composition_config_yaml_filepath,
            env_file_path=environment_config_yaml_filepath
        )
        return cls(config)
