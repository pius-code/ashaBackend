# flake8: noqa
# type: ignore


from pydantic import BaseModel, Field


class Workflow(BaseModel):
    workflow_id: str = Field(
        description="Unique ID combining short description and random chars. Example: 'morning_light_9x2k'"
    )
    asha_id: str = Field(
        description="The ASHA ID from get_user_projects_and_devices(). Never guess this."
    )
    cron_expr: str = Field(
        description="Cron expression. Format: 'minute hour day month day_of_week'. Example: '0 6 * * *' = every day at 6am"
    )
    actions: list[dict] = Field(
        description="List of MQTT payloads. Follow bus type rules from publish_command. Example: [{'pin': 18, 'action': 'digital', 'value': 1}]"
    )
