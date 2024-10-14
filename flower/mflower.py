from mcelery.celery import celery_app
from mcelery.infer import register_infer_tasks

register_infer_tasks()
app = celery_app
