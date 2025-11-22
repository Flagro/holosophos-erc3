import time
from typing import Annotated, List, Union, Literal
from annotated_types import MaxLen, MinLen
from pydantic import BaseModel, Field
from erc3 import corporate, ApiException, TaskInfo, ERC3
from openai import OpenAI

client = OpenAI()


class ReportTaskCompletion(BaseModel):
    tool: Literal["report_completion"]
    completed_steps_laconic: List[str]
    code: Literal["completed", "failed"]


class NextStep(BaseModel):
    current_state: str
    # we'll use only the first step, discarding all the rest.
    plan_remaining_steps_brief: Annotated[List[str], MinLen(1), MaxLen(5)] = Field(
        ...,
        description="explain your thoughts on how to accomplish - what steps to execute",
    )
    # now let's continue the cascade and check with LLM if the task is done
    task_completed: bool
    # Routing to one of the tools to execute the first remaining step
    # if task is completed, model will pick ReportTaskCompletion
    function: Union[
        corporate.ReportTaskCompletion,
        corporate.Req_ListEmployees,
        corporate.Req_GetEmployeeDetails,
        corporate.Req_UpdateEmployeeStatus,
        corporate.Req_CreateProject,
        corporate.Req_ListProjects,
        corporate.Req_AssignTask,
        corporate.Req_GetBudgetReport,
    ] = Field(..., description="execute first remaining step")


system_prompt = """
You are a corporate management assistant helping with employee and project management tasks.

- Clearly report when tasks are done.
- You can list employees, get their details, and update their status.
- You can create projects, list them, and assign tasks to employees.
- You can retrieve budget reports for departments.
- Always verify information before making changes to employee status or project assignments.
"""

CLI_RED = "\x1b[31m"
CLI_GREEN = "\x1b[32m"
CLI_CLR = "\x1b[0m"


def run_agent(model: str, api: ERC3, task: TaskInfo):
    """
    Corporate management agent template.

    When the actual corporate API is available from erc3 package:
    - Replace placeholder request models (Req_*) with actual API models
    - Update the dispatch method to use the real corporate API client
    - Adjust system_prompt to match actual corporate API capabilities
    """

    # TODO: Replace with actual corporate API client when available
    # corporate_api = api.get_corporate_client(task)
    # For now, we'll use a placeholder that simulates the dispatch pattern

    class PlaceholderCorporateAPI:
        """Placeholder API - replace with actual corporate API client"""

        def dispatch(self, request):
            # Simulate API responses based on request type
            # Replace this entire class with actual API client
            request_type = request.__class__.__name__

            # Mock responses for different request types
            if request_type == "Req_ListEmployees":
                return BaseModel.model_construct(_fields_set={"employees", "total"})
            elif request_type == "Req_GetEmployeeDetails":
                return BaseModel.model_construct(
                    _fields_set={"employee_id", "name", "department"}
                )
            # Add more mock responses as needed

            return BaseModel.model_construct(_fields_set={"status": "success"})

    corporate_api = PlaceholderCorporateAPI()

    # log will contain conversation context for the agent within task
    log = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task.task_text},
    ]

    # let's limit number of reasoning steps by 20, just to be safe
    for i in range(20):
        step = f"step_{i + 1}"
        print(f"Next {step}... ", end="")

        started = time.time()

        completion = client.beta.chat.completions.parse(
            model=model,
            response_format=NextStep,
            messages=log,
            max_completion_tokens=10000,
        )

        api.log_llm(
            task_id=task.task_id,
            model="openai/" + model,  # log in OpenRouter format
            duration_sec=time.time() - started,
            usage=completion.usage,
        )

        job = completion.choices[0].message.parsed

        # if SGR wants to finish, then quit loop
        if isinstance(job.function, ReportTaskCompletion):
            print(f"[blue]agent {job.function.code}[/blue]. Summary:")
            for s in job.function.completed_steps_laconic:
                print(f"- {s}")
            break

        # print next step for debugging
        print(job.plan_remaining_steps_brief[0], f"\n  {job.function}")

        # Let's add tool request to conversation history as if OpenAI asked for it.
        # a shorter way would be to just append `job.model_dump_json()` entirely
        log.append(
            {
                "role": "assistant",
                "content": job.plan_remaining_steps_brief[0],
                "tool_calls": [
                    {
                        "type": "function",
                        "id": step,
                        "function": {
                            "name": job.function.__class__.__name__,
                            "arguments": job.function.model_dump_json(),
                        },
                    }
                ],
            }
        )

        # now execute the tool by dispatching command to our handler
        try:
            result = corporate_api.dispatch(job.function)
            txt = result.model_dump_json(exclude_none=True, exclude_unset=True)
            print(f"{CLI_GREEN}OUT{CLI_CLR}: {txt}")
        except ApiException as e:
            txt = e.detail
            # print to console as ascii red
            print(f"{CLI_RED}ERR: {e.api_error.error}{CLI_CLR}")
        except Exception as e:
            # Catch any other exceptions during placeholder API usage
            txt = f"Error: {str(e)}"
            print(f"{CLI_RED}ERR: {txt}{CLI_CLR}")

        # and now we add results back to the conversation history, so that agent
        # will be able to act on the results in the next reasoning step.
        log.append({"role": "tool", "content": txt, "tool_call_id": step})
