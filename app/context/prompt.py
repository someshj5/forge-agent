class PromptBuilder:
    def build(self, task: str, context: str) -> list[dict]:
        system_prompt ="""
        You are a coding agent.
        Use the provided repository context to understand the user's task.
        Do not assume files or code that are not provided.
        Return exactly one valid JSON action according to the available action schema.
        """.strip()

        system={"role":"system","content":system_prompt}
        
        user={"role":"user","content":f"Task:\n{task} \n\n Repository Context:\n{context}"}
        
        return [system, user]