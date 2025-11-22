import logging
from typing import Optional, Sequence

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODEL_NAME: str = "deepseek/deepseek-chat-v3-0324"
    MAX_COMPLETION_TOKENS: int = 16384
    MAX_HISTORY_TOKENS: int = 131072

    ACADEMIA_MCP_URL: str = "http://0.0.0.0:5056/mcp"
    MLE_KIT_MCP_URL: str = "http://0.0.0.0:5057/mcp"

    ENABLE_PHOENIX: bool = False
    PHOENIX_URL: str = "http://localhost:6006"
    PHOENIX_PROJECT_NAME: str = "holosophos"
    PHOENIX_ENDPOINT: Optional[str] = None

    PORT: int = 5055
    WORKSPACE_DIR: str = "./workdir"

    VERBOSITY_LEVEL: int = logging.INFO

    # CodeArkt settings
    PLANNING_LAST_N: int = 50
    PLANNING_CONTENT_MAX_LENGTH: int = 4000
    DEFAULT_MAX_ITERATIONS: int = 20
    MAX_LENGTH_TRUNCATE_CONTENT: int = 20000

    AGENT_TOOL_PREFIX: str = "agent__"

    DEFAULT_SERVER_HOST: str = "0.0.0.0"
    DEFAULT_SERVER_PORT: int = 5055

    # Executor settings
    CODEARKT_EXECUTOR_URL: Optional[str] = None
    EXECUTOR_IMAGE: str = (
        "phoenix120/codearkt_http@sha256:e00d11db4bc70918f61ebd53e19b0b2f382af6165346322af401b701118404e1"
    )
    DOCKER_MEM_LIMIT: str = "1g"
    DOCKER_CPU_QUOTA: int = 50000
    DOCKER_CPU_PERIOD: int = 100000
    DOCKER_CLEANUP_TIMEOUT: int = 10
    DOCKER_PIDS_LIMIT: int = 256
    DOCKER_NET_NAME: str = "codearkt_sandbox_net"

    # Timeout settings
    EVENT_BUS_STREAM_TIMEOUT: int = 24 * 60 * 60
    FINISH_WAIT_TIMEOUT: int = 10
    EXEC_TIMEOUT: int = 24 * 60 * 60
    PROXY_SSE_READ_TIMEOUT: int = 12 * 60 * 60

    # OpenRouter settings
    BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY: str = ""
    HTTP_REFERRER: str = "https://github.com/IlyaGusev/codearkt/"
    X_TITLE: str = "CodeArkt"

    MANAGER_MAX_ITERATIONS: int = 100
    MANAGER_PLANNING_INTERVAL: int = 9
    MANAGER_TOOLS: Sequence[str] = (
        "bash",
        "install_with_apt",
        "text_editor",
        "describe_image",
        "speech_to_text",
    )

    LIBRARIAN_MAX_ITERATIONS: int = 150
    LIBRARIAN_PLANNING_INTERVAL: int = 9
    LIBRARIAN_TOOLS: Sequence[str] = (
        "arxiv_download",
        "arxiv_search",
        "anthology_search",
        "s2_get_citations",
        "s2_get_references",
        "s2_get_info",
        "s2_search",
        "hf_datasets_search",
        "document_qa",
        "web_search",
        "visit_webpage",
        "text_editor",
        "describe_image",
        "yt_transcript",
    )

    MLE_SOLVER_MAX_ITERATIONS: int = 200
    MLE_SOLVER_PLANNING_INTERVAL: int = 14
    MLE_SOLVER_TOOLS_REMOTE: Sequence[str] = (
        "remote_bash",
        "remote_text_editor",
        "remote_download",
        "llm_proxy_remote",
        "hf_datasets_search",
        "web_search",
        "visit_webpage",
        "describe_image",
    )
    MLE_SOLVER_TOOLS: Sequence[str] = (
        "bash",
        "install_with_apt",
        "text_editor",
        "llm_proxy_local",
        "hf_datasets_search",
        "web_search",
        "visit_webpage",
        "describe_image",
    )
    MLE_SOLVER_IS_REMOTE: bool = False

    WRITER_MAX_ITERATIONS: int = 100
    WRITER_PLANNING_INTERVAL: int = 9
    WRITER_TOOLS: Sequence[str] = (
        "get_latex_template",
        "get_latex_templates_list",
        "compile_latex",
        "bash",
        "install_with_apt",
        "text_editor",
        "read_pdf",
        "describe_image",
    )

    PROPOSER_MAX_ITERATIONS: int = 200
    PROPOSER_PLANNING_INTERVAL: int = 9
    PROPOSER_TOOLS: Sequence[str] = (
        "web_search",
        "visit_webpage",
        "document_qa",
        "extract_bitflip_info",
        "generate_research_proposals",
        "score_research_proposals",
        "text_editor",
    )

    REVIEWER_MAX_ITERATIONS: int = 50
    REVIEWER_PLANNING_INTERVAL: int = 9
    REVIEWER_TOOLS: Sequence[str] = (
        "review_pdf_paper",
        "download_pdf_paper",
        "visit_webpage",
        "web_search",
        "bash",
        "text_editor",
        "describe_image",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", case_sensitive=False, extra="ignore"
    )

    @field_validator("OPENROUTER_API_KEY")  # type: ignore
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("OPENROUTER_API_KEY must not be empty")
        return v

    @property
    def RESOLVED_PHOENIX_ENDPOINT(self) -> str:
        if self.PHOENIX_ENDPOINT:
            return str(self.PHOENIX_ENDPOINT)
        return f"{self.PHOENIX_URL}/v1/traces"


settings = Settings()
