from debussy_framework.v3.hooks.db_api_hook import DbApiInterface
from debussy_framework.v3.hooks.storage_hook import StorageHookInterface
from debussy_framework.v3.operators.storage_to_rdbms import StorageToRdbmsOperator

from debussy_concert.core.motif.motif_base import MotifBase


class StorageToRdbmsQueryMotif(MotifBase):
    destination_table = None

    def __init__(self,
                 dbapi_hook: DbApiInterface,
                 storage_hook: StorageHookInterface,
                 destination_table: str,
                 name=None,
                 **op_kw_args):
        super().__init__(name=name)

        self.dbapi_hook = dbapi_hook
        self.storage_hook = storage_hook
        self.destination_table = destination_table
        self.op_kw_args = op_kw_args

    def setup(self, storage_uri_prefix=None):
        self.storage_file_uri = storage_uri_prefix
        return self

    def build(self, dag, task_group):
        storage_to_rdbms_operator = StorageToRdbmsOperator(
            task_id=self.name,
            dbapi_hook=self.dbapi_hook,
            storage_hook=self.storage_hook,
            storage_file_uri=self.storage_file_uri,
            table_name=self.destination_table,
            dag=dag, task_group=task_group,
            **self.op_kw_args
        )

        return storage_to_rdbms_operator
