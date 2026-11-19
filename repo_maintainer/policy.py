from dataclasses import dataclass, field

@dataclass(frozen=True)
class MaintainerPolicy:
    allowed_repositories: frozenset[str] = field(default_factory=frozenset)
    allowed_base_branches: frozenset[str] = field(default_factory=lambda: frozenset({"main"}))
    allowed_test_commands: tuple[tuple[str, ...], ...] = ()
    allow_branch_creation: bool = False
    allow_file_writes: bool = False
    allow_pull_request_creation: bool = False
    allow_merge: bool = False
    allow_deployment: bool = False
    allow_network_tests: bool = False
    max_changed_files: int = 20
    def validate_repository(self, repository: str) -> None:
        if repository not in self.allowed_repositories:
            raise PermissionError(f"repository is not allowlisted: {repository}")
    def validate_base(self, base_ref: str) -> None:
        if base_ref not in self.allowed_base_branches:
            raise PermissionError(f"base branch is not allowlisted: {base_ref}")
    def validate_test_command(self, command: tuple[str, ...]) -> None:
        if not command or command not in self.allowed_test_commands:
            raise PermissionError("test command is not explicitly allowlisted")
    def require(self, capability: str) -> None:
        mapping = {"branch_creation": self.allow_branch_creation, "file_writes": self.allow_file_writes,
                   "pull_request_creation": self.allow_pull_request_creation, "merge": self.allow_merge,
                   "deployment": self.allow_deployment, "network_tests": self.allow_network_tests}
        if capability not in mapping:
            raise ValueError(f"unknown capability: {capability}")
        if not mapping[capability]:
            raise PermissionError(f"capability is disabled by policy: {capability}")
