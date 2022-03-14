from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.google.cloud.operators.dataproc import (
     DataprocCreateClusterOperator, DataprocDeleteClusterOperator)


class DataprocClusterHandlerMixin:
    def delete_dataproc_cluster(self, dag, task_group):
        delete_dataproc_cluster = DataprocDeleteClusterOperator(
            task_id="delete_dataproc_cluster",
            project_id=self.config.environment.project,
            cluster_name=self.cluster_name,
            region=self.config.environment.region,
            trigger_rule=TriggerRule.ALL_DONE,
            dag=dag,
            task_group=task_group
        )
        return delete_dataproc_cluster

    def create_dataproc_cluster(self, dag, task_group):
        create_dataproc_cluster = DataprocCreateClusterOperator(
            task_id="create_dataproc_cluster",
            project_id=self.config.environment.project,
            cluster_config=self.cluster_config,
            region=self.config.environment.region,
            cluster_name=self.cluster_name,
            dag=dag,
            task_group=task_group
        )

        return create_dataproc_cluster
