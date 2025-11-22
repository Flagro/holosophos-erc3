"""
ERC3 Agent Runner

This script runs ERC3 agents for the AI Agents in Action competition.
It supports both the store and corporate benchmarks using Schema-Guided Reasoning.

Usage:
    # Set up your environment variables
    export OPENAI_API_KEY=sk-...
    export ERC3_API_KEY=key-...

    # Run with default settings (store benchmark, gpt-4o)
    python main.py

    # Or specify custom settings
    python main.py --benchmark corporate --model gpt-4o-mini --workspace my-workspace
"""

import textwrap
import argparse
from erc3 import ERC3
from holosophos_erc.erc_agents.store_agent import run_agent as run_store_agent
from holosophos_erc.erc_agents.corporate_agent import run_agent as run_corporate_agent


def main(benchmark: str = "store", model: str = "gpt-4o", workspace: str = "my"):
    """
    Run ERC3 agents for the specified benchmark.

    Args:
        benchmark: The benchmark to run ('store' or 'corporate')
        model: The OpenAI model to use (default: 'gpt-4o')
        workspace: The ERC3 workspace name (default: 'my')
    """
    core = ERC3()

    # Start session with metadata
    res = core.start_session(
        benchmark=benchmark,
        workspace=workspace,
        name="Simple SGR Agent",
        architecture="NextStep SGR Agent with OpenAI",
    )

    status = core.session_status(res.session_id)
    print(f"Session has {len(status.tasks)} tasks")

    for task in status.tasks:
        print("=" * 40)
        print(f"Starting Task: {task.task_id} ({task.spec_id}): {task.task_text}")
        # start the task
        core.start_task(task)
        try:
            if benchmark == "store":
                run_store_agent(model, core, task)
            elif benchmark == "corporate":
                run_corporate_agent(model, core, task)
            else:
                raise ValueError(f"Unknown benchmark: {benchmark}")
        except Exception as e:
            print(f"Error running agent: {e}")

        result = core.complete_task(task)
        if result.eval:
            explain = textwrap.indent(result.eval.logs, "  ")
            print(f"\nSCORE: {result.eval.score}\n{explain}\n")

    core.submit_session(res.session_id)
    print(f"\n✓ Session {res.session_id} completed and submitted!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run ERC3 agents for AI Agents in Action competition"
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="store",
        choices=["store", "corporate"],
        help="Benchmark to run (default: store)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default="my",
        help="ERC3 workspace name (default: my)",
    )

    args = parser.parse_args()
    main(benchmark=args.benchmark, model=args.model, workspace=args.workspace)
