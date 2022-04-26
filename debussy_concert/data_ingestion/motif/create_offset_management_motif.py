from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator

from debussy_framework.v2.operators.datastore import (
    DatastoreGetEntityOperator,
    DatastoreUpdateEntityOperator
)
from debussy_framework.v2.operators.bigquery import (
    BigQueryGetMaxFieldOperator
)

from debussy_concert.core.motif.motif_base import MotifBase


class CreateOffsetManagementMotif(MotifBase):
    def __init__(
            self, ds_project,
            namespace,
            kind,
            filters,
            end_project,
            end_dataset,
            end_table,
            offset_field_id,
            offset_field_type,
            offset_field_format_string,
            entity_updater_callable,
            name=None
    ):
        self.ds_project = ds_project
        self.namespace = namespace
        self.kind = kind
        self.filters = filters
        self.end_project = end_project
        self.end_dataset = end_dataset
        self.end_table = end_table
        self.offset_field_id = offset_field_id
        self.offset_field_type = offset_field_type
        self.offset_field_format_string = offset_field_format_string
        self.entity_updater_callable = entity_updater_callable
        super().__init__(name=name)

    def setup(self):
        pass

    def build(self, dag, phrase_group):
        task_group = TaskGroup(group_id=self.name, dag=dag, parent_group=phrase_group)
        get_datastore_entity = self.get_datastore_entity(dag, task_group)
        get_max_offset_field_value = self.get_max_offset_field_value(dag, task_group)
        update_datastore_entity_offset = self.update_datastore_entity_offset(
            dag, task_group, get_datastore_entity.task_id, get_max_offset_field_value.task_id)
        update_datastore_entity = self.update_datastore_entity(
            dag, task_group, update_datastore_entity_offset.task_id)
        return self.workflow_service.chain_tasks(
            get_datastore_entity,
            get_max_offset_field_value,
            update_datastore_entity_offset,
            update_datastore_entity
        )

    def update_datastore_entity(self, dag, task_group, update_datastore_entity_offset_id):
        update_datastore_entity = DatastoreUpdateEntityOperator(
            task_id="update_datastore_entity",
            project=self.ds_project,
            namespace=self.namespace,
            kind=self.kind,
            entity_json_str=f"{{{{ task_instance.xcom_pull('{update_datastore_entity_offset_id}') }}}}",
            dag=dag,
            task_group=task_group
        )
        return update_datastore_entity

    def update_datastore_entity_offset(self, dag, task_group, get_datastore_entity_id, get_max_offset_field_value_id):
        update_datastore_entity_offset = PythonOperator(
            task_id="update_datastore_entity_offset",
            python_callable=self.entity_updater_callable,
            op_kwargs={
                "entity_json_str": f"{{{{ task_instance.xcom_pull('{get_datastore_entity_id}') }}}}",
                "offset_value": f"{{{{ task_instance.xcom_pull('{get_max_offset_field_value_id}') }}}}",
            },
            dag=dag,
            task_group=task_group
        )

        return update_datastore_entity_offset

    def get_max_offset_field_value(self, dag, task_group):
        get_max_offset_field_value = BigQueryGetMaxFieldOperator(
            task_id="get_max_offset_field_value",
            project_id=self.end_project,
            dataset_id=self.end_dataset,
            table_id=self.end_table,
            field_id=self.offset_field_id,
            field_type=self.offset_field_type,
            format_string=self.offset_field_format_string,
            dag=dag,
            task_group=task_group
        )

        return get_max_offset_field_value

    def get_datastore_entity(self, dag, task_group):
        get_datastore_entity = DatastoreGetEntityOperator(
            task_id="get_datastore_entity",
            project=self.ds_project,
            namespace=self.namespace,
            kind=self.kind,
            filters=self.filters,
            dag=dag,
            task_group=task_group
        )
        return get_datastore_entity
