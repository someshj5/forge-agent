from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    success: bool
    agent: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Agent(ABC):
    name: str

    @abstractmethod
    def run(self, state) -> AgentResult:
        raise NotImplementedError