"""Apache Airflow DAG integration."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
import json


class AirflowIntegration:
    """
    Apache Airflow integration for workflow orchestration.

    Airflow is a platform to programmatically author, schedule and monitor workflows.
    """

    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Airflow integration.

        Args:
            base_url: Airflow web server URL
            username: Airflow username
            password: Airflow password
        """
        self.base_url = base_url
        self.auth = (username, password) if username and password else None
        self.session = requests.Session()

    def trigger_dag(
        self,
        dag_id: str,
        conf: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger an Airflow DAG.

        Args:
            dag_id: DAG identifier
            conf: Configuration parameters for the DAG run

        Returns:
            Result dictionary

        Example:
            >>> airflow = AirflowIntegration("http://localhost:8080", "admin", "admin")
            >>> result = airflow.trigger_dag("my_dag", {"param": "value"})
        """
        try:
            url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns"

            payload = {
                "conf": conf or {},
                "dag_run_id": f"manual_{datetime.now().isoformat()}"
            }

            response = self.session.post(
                url,
                json=payload,
                auth=self.auth,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            return {
                "success": True,
                "dag_id": dag_id,
                "dag_run_id": result.get('dag_run_id'),
                "state": result.get('state'),
                "execution_date": result.get('execution_date')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_dag_status(self, dag_id: str, dag_run_id: str) -> Dict[str, Any]:
        """Get status of a DAG run."""
        try:
            url = f"{self.base_url}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"

            response = self.session.get(url, auth=self.auth, timeout=30)
            response.raise_for_status()

            result = response.json()

            return {
                "success": True,
                "dag_id": dag_id,
                "dag_run_id": dag_run_id,
                "state": result.get('state'),
                "start_date": result.get('start_date'),
                "end_date": result.get('end_date')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_dags(self) -> Dict[str, Any]:
        """List all DAGs."""
        try:
            url = f"{self.base_url}/api/v1/dags"

            response = self.session.get(url, auth=self.auth, timeout=30)
            response.raise_for_status()

            result = response.json()
            dags = result.get('dags', [])

            return {
                "success": True,
                "total_dags": len(dags),
                "dags": [
                    {
                        "dag_id": dag.get('dag_id'),
                        "is_active": dag.get('is_active'),
                        "is_paused": dag.get('is_paused')
                    }
                    for dag in dags
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def pause_dag(self, dag_id: str) -> Dict[str, Any]:
        """Pause a DAG."""
        return self._set_dag_state(dag_id, is_paused=True)

    def unpause_dag(self, dag_id: str) -> Dict[str, Any]:
        """Unpause a DAG."""
        return self._set_dag_state(dag_id, is_paused=False)

    def _set_dag_state(self, dag_id: str, is_paused: bool) -> Dict[str, Any]:
        """Set DAG paused state."""
        try:
            url = f"{self.base_url}/api/v1/dags/{dag_id}"

            payload = {"is_paused": is_paused}

            response = self.session.patch(
                url,
                json=payload,
                auth=self.auth,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()

            return {
                "success": True,
                "dag_id": dag_id,
                "is_paused": is_paused
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if hasattr(self, 'session') and self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()

    @staticmethod
    def generate_dag_template(
        dag_id: str,
        description: str,
        schedule: str = "@daily",
        tasks: List[str] = None
    ) -> str:
        """
        Generate Airflow DAG Python code template.

        Args:
            dag_id: DAG identifier
            description: DAG description
            schedule: Cron schedule or preset
            tasks: List of task names

        Returns:
            Python code as string

        Example:
            >>> code = AirflowIntegration.generate_dag_template(
            ...     "my_dag",
            ...     "My workflow",
            ...     tasks=["extract", "transform", "load"]
            ... )
        """
        tasks = tasks or ["task1", "task2"]

        template = f'''"""
{description}
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {{
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

dag = DAG(
    '{dag_id}',
    default_args=default_args,
    description='{description}',
    schedule_interval='{schedule}',
    catchup=False,
)

# Define task functions
'''

        for task in tasks:
            template += f'''
def {task}_function(**context):
    """Task: {task}"""
    print(f"Executing {task}")
    # Add your task logic here
    return "{task} completed"

{task}_task = PythonOperator(
    task_id='{task}',
    python_callable={task}_function,
    dag=dag,
)
'''

        # Add dependencies
        if len(tasks) > 1:
            template += "\n# Set task dependencies\n"
            for i in range(len(tasks) - 1):
                template += f"{tasks[i]}_task >> {tasks[i+1]}_task\n"

        return template


# Example Airflow DAG use cases:
"""
Example Airflow DAG Workflows:

1. ETL Pipeline:
   - Extract from API → Transform Data → Load to Database

2. ML Training Pipeline:
   - Fetch Data → Preprocess → Train Model → Evaluate → Deploy

3. Data Quality Pipeline:
   - Extract → Validate → Clean → Load → Generate Report

4. Multi-Source Data Aggregation:
   - [Fetch API1, Fetch API2, Fetch DB] → Merge → Process → Store

5. Report Generation:
   - Query Data → Generate Charts → Create PDF → Email Report
"""
