import logging

from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from debussy_framework.v3.operators.basic import StartOperator

from debussy_concert.core.motif.motif_base import MotifBase


class StartMotif(MotifBase):
    def __init__(self, name=None) -> None:
        super().__init__(name=name)

    def build(self, dag, parent_task_group):
        task_group = TaskGroup(group_id=self.name, dag=dag, parent_group=parent_task_group)
        start_dag = StartOperator(phase="dag", dag=dag, task_group=task_group)
        log_input = PythonOperator(
            task_id='log_input',
            python_callable=lambda **x: logging.info(x),
            op_kwargs={'config': self.config},
            dag=dag,
            task_group=task_group
        )
        start_dag >> log_input
        return task_group
