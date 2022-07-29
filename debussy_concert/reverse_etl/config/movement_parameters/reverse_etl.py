from dataclasses import dataclass


from debussy_concert.core.config.movement_parameters.base import MovementParametersBase
from typing import Optional


@dataclass(frozen=True)
class OutputConfig:
    format: str
    file_name: str


@dataclass(frozen=True)
class CsvFile(OutputConfig):
    field_delimiter: str
    print_header: bool = True


class AvroFile(OutputConfig):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("AvroFile is not implemented yet")


class ParquetFile(OutputConfig):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("ParquetFile is not implemented yet")


class JsonFile(OutputConfig):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("JsonFile is not implemented yet")


def output_factory(output_config):
    format: str = output_config['format']
    mapping = {
        'csv': CsvFile,
        'avro': AvroFile,
        'parquet': ParquetFile,
        'json': JsonFile
    }
    output_cls = mapping.get(format.lower())
    if output_cls is None:
        raise TypeError(f'Format `{format}` is not supported')
    return output_cls(**output_config)


@dataclass(frozen=True)
class ReverseEtlMovementParameters(MovementParametersBase):
    name: str
    reverse_etl_query: str
    reverse_etl_dataset_partition_type: str
    reverse_etl_dataset_partition_field: str
    destination_type: str
    output_config: OutputConfig
    destination_connection_id: str
    extraction_query_from_temp: str
    destination_uri: str    

    def __post_init__(self):
        output_config = output_factory(self.output_config)
        # hack for frozen dataclass https://stackoverflow.com/a/54119384
        # overwriting output_config with output_factory instance
        object.__setattr__(self, 'output_config', output_config)

    @classmethod
    def load_from_dict(cls, movement_parameters):
        cls_instance = cls(**movement_parameters)
        return cls_instance
