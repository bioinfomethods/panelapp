from celery._state import get_current_task
from pythonjsonlogger.jsonlogger import JsonFormatter


class TaskFormatter(JsonFormatter):
    """Formatter for tasks, adding the task name and id."""

    def process_log_record(self, log_record):
        # add celery task name and id to the log data

        task = get_current_task()
        if task and task.request:
            log_record["task_id"] = task.request.id
            log_record["task_name"] = task.name

        return log_record
