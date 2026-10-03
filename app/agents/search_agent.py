from app.agents.base import Agent, AgentResult
from app.context.engine import ContextEngine
from app.tools.web_search import WebSearchTool
from app.skills.context import SkillContextLoader
from app.skills.retriever import SkillRetriever

class SearchAgent(Agent):
    name = "search"

    def __init__(
        self,
        context_engine=None,
        web_search_tool=None,
        skill_retriever=None,
        skill_context_loader=None,
    ):
        self.context_engine = context_engine or ContextEngine()
        self.web_search_tool = web_search_tool
        self.skill_retriever = skill_retriever
        self.skill_context_loader = skill_context_loader

    def _needs_web_search(self, task: str) -> bool:
        keywords = [
            "latest",
            "documentation",
            "docs",
            "official",
            "current",
            "how does",
            "how to use",
            "recommended",
            "release",
            "version",
            "api",
        ]

        task_lower = task.lower()

        return any(
            keyword in task_lower
            for keyword in keywords
        )

    def _build_skill_query(self, state) -> str:
        parts = [
            state.task,
            state.repository,
            state.target_symbol or "",
        ]

        for path in state.relevant_files:
            parts.append(path)

        repository = state.repository.lower()

        if "django" in repository.lower():
            parts.extend([
                "Django",
                "Django framework",
            ])


        for path in state.relevant_files:
            if path.endswith(".py"):
                parts.append("Python")

            if path.endswith("urls.py"):
                parts.extend([
                    "Django URL configuration",
                    "Django URL routing",
                    "urlpatterns",
                ])

            if path.endswith("models.py"):
                parts.append("Django ORM models")

            if path.endswith("serializers.py"):
                parts.append("Django REST Framework serializers")

            if path.endswith("views.py"):
                parts.append("Django views")

        return " ".join(
            part for part in parts if part
        )

    def _retrieve_skills(self, state) -> None:
        if not self.skill_retriever:
            return

        if not self.skill_context_loader:
            return

        skill_query = self._build_skill_query(state)

        skill_results = self.skill_retriever.retrieve(
        skill_query,
            limit=10,
        )

        print("\n========== SKILL RETRIEVAL ==========")
        print(f"Query: {skill_query}")

        for index, result in enumerate(skill_results, start=1):
            print(
                f"{index:2}. "
                f"{result.skill.name:<45} "
                f"score={result.score}"
            )

        django_result = next(
            (
                result
                for result in self.skill_retriever.registry.search(
                    skill_query,
                    limit=len(
                        self.skill_retriever.registry.all()
                    ),
                )
                if result.skill.name == "django-pro"
            ),
            None,
        )

        if django_result:
            print(
                f"\nDjango-pro rank/score: "
                f"{django_result.score}"
            )
        else:
            print("\ndjango-pro: NO MATCH")

        selected_skills = [
            result.skill
            for result in skill_results
        ]

        state.selected_skills = [
            skill.name
            for skill in selected_skills
        ]

        state.skill_context = (
            self.skill_context_loader.load_many(
                selected_skills
            )
        )


    def run(self, state) -> AgentResult:
        state.current_agent = self.name

        # ---------------------------------------------------------
        # 1. Determine the target symbol from the task.
        # ---------------------------------------------------------
        search_query = self._build_search_query(
            state.task
        )

        state.target_symbol = search_query

        print(
            f"[SearchAgent] task: {state.task}"
        )
        print(
            f"[SearchAgent] search_query: {search_query}"
        )

        # ---------------------------------------------------------
        # 2. Retrieve repository context.
        # ---------------------------------------------------------
        context = self.context_engine.get_context(
            search_query,
            state.repository,
        )

        print(
            f"[SearchAgent] context: {context}"
        )

        relevant_files = []

        for item in context:
            path = item.get("path")

            if path and path not in relevant_files:
                relevant_files.append(path)

        state.relevant_files = relevant_files

        # ---------------------------------------------------------
        # 3. Retrieve relevant skills AFTER repository context.
        # ---------------------------------------------------------
        self._retrieve_skills(state)

        # ---------------------------------------------------------
        # 4. Optional web search.
        # ---------------------------------------------------------
        web_results = []

        if (
            self.web_search_tool
            and self._needs_web_search(state.task)
        ):
            search_response = self.web_search_tool.search(
                state.task
            )

            if isinstance(search_response, dict):
                web_results = search_response.get(
                    "results",
                    []
                )
            else:
                web_results = search_response

        state.web_results = web_results
        # ---------------------------------------------------------
        # 5. Return the search result.
        # ---------------------------------------------------------
        return AgentResult(
            success=True,
            agent=self.name,
            data={
                "relevant_files": state.relevant_files,
                "target_symbol": state.target_symbol,
                "selected_skills": state.selected_skills,
                "skill_context": state.skill_context,
                "web_results": state.web_results,
            },
        )

    def _build_search_query(self, task: str) -> str:
        """
        Build a repository-oriented search query from the user task.

        V1 intentionally uses lightweight heuristics.
        Later this can become an LLM-assisted query planner.
        """
        task_lower = task.lower()

        known_symbols = [
            "urlpatterns",
            "installed_apps",
            "databases",
            "execute_from_command_line",
            "settings",
            "urls",
            "views",
            "models",
            "serializers",
            "views.py",
            "models.py",
            "settings.py",
            "urls.py",
        ]

        for symbol in known_symbols:
            if symbol.lower() in task_lower:
                return symbol

        return task
