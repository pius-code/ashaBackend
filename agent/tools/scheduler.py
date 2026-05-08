from core.scheduler import scheduler
from agent.tools.pubSub_tools import publish_to_device
from agent.schema.workflow import Workflow
from datetime import datetime



def execute_workflow(asha_id: str, commands: list):
    for command in commands:
        publish_to_device(asha_id, command)
        print(f"Executed command: {command}")

# TODO: for tasks lesser than 1 min use interval(check readme for more info)
def create_scheduled_workflow(workflow: Workflow):
    asha_id = workflow.asha_id
    commands = workflow.actions
    cron_expr = workflow.cron_expr
    
    # parse cron expression
    parts = cron_expr.split()
    # "0 6 * * *" → minute=0, hour=6, day=*, month=*, day_of_week=*
    
    scheduler.add_job(
        execute_workflow,
        'cron',
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        args=[asha_id, commands], 
        id=workflow.workflow_id,
        next_run_time=datetime.now() 
    )
    print(f"Workflow scheduled: {workflow.workflow_id}")

def delete_workflow(workflow_id: str):
    scheduler.remove_job(workflow_id)
    print(f"Workflow deleted: {workflow_id}")
