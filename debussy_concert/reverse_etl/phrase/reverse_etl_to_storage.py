from debussy_concert.core.phrase.phrase_base import PhraseBase
from debussy_concert.reverse_etl.config.reverse_etl import ConfigReverseEtl
from debussy_concert.core.config.movement_parameters.base import MovementParametersType


class DataWarehouseReverseEtlToTempToStoragePhrase(PhraseBase):
    config: ConfigReverseEtl

    def __init__(
        self,
        datawarehouse_reverse_etl_to_temp_table_motif,
        export_temp_table_to_storage_motif,
        name=None
    ) -> None:
        self.datawarehouse_reverse_etl_to_temp_table_motif = datawarehouse_reverse_etl_to_temp_table_motif
        self.export_temp_table_to_storage_motif = export_temp_table_to_storage_motif
        motifs = [self.datawarehouse_reverse_etl_to_temp_table_motif,
                  self.export_temp_table_to_storage_motif]
        super().__init__(name=name,
                         motifs=motifs)

    @property
    def temp_table_uri(self):
        return (f"{self.config.environment.project}."
                f"{self.config.environment.temp_dataset}."
                f"{self.config.name}_{self.movement_parameters.name}")

    def setup(self,
              movement_parameters: MovementParametersType,
              extraction_query, storage_uri_prefix):
        self.movement_parameters = movement_parameters
        self.datawarehouse_reverse_etl_to_temp_table_motif.setup(
            sql_query=extraction_query,
            destination_table=self.temp_table_uri)
        self.export_temp_table_to_storage_motif.setup(
            source_table_uri=self.temp_table_uri,
            destination_uris=[storage_uri_prefix])
        return self


class DataWarehouseReverseEtlToStoragePhrase(PhraseBase):
    config: ConfigReverseEtl

    def __init__(
        self,
        datawarehouse_reverse_etl_to_table_motif,
        export_table_to_storage_motif,
        name=None
    ) -> None:
        self.datawarehouse_reverse_etl_to_table_motif = datawarehouse_reverse_etl_to_table_motif
        self.export_table_to_storage_motif = export_table_to_storage_motif
        motifs = [self.datawarehouse_reverse_etl_to_table_motif, self.export_table_to_storage_motif]
        super().__init__(name=name,
                         motifs=motifs)

    @property
    def reverse_etl_table_uri(self):
        return (f"{self.config.environment.project}."
                f"{self.config.environment.reverse_etl_dataset}."
                f"{self.config.name}_{self.movement_parameters.name}")

    def setup(self,
              movement_parameters: MovementParametersType,
              extract_query, storage_uri_prefix):
        self.movement_parameters = movement_parameters
        self.datawarehouse_reverse_etl_to_table_motif.setup(
            sql_query=extract_query,
            destination_table=self.reverse_etl_table_uri)
        self.export_table_to_storage_motif.setup(
            source_table_uri=self.reverse_etl_table_uri,
            destination_uris=[storage_uri_prefix])
        return self
