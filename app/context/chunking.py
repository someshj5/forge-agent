import ast


class PythonChunker:
    """
    Splits a Python source file into top-level structural chunks.

    Each top-level AST node becomes one retrieval unit.
    """

    def chunk(self, path: str, content: str) -> list[dict]:
        if not content.strip():
            return []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If the file cannot be parsed, fall back to treating
            # the entire file as a single chunk.
            return [
                {
                    "path": path,
                    "chunk_id": f"{path}:1",
                    "content": content,
                    "start_line": 1,
                    "end_line": len(content.splitlines()),
                }
            ]

        lines = content.splitlines(keepends=True)

        chunks = []

        for index, node in enumerate(tree.body, start=1):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)

            chunk_content = "".join(
                lines[start_line - 1:end_line]
            )

            chunks.append(
                {
                    "path": path,
                    "chunk_id": f"{path}:{start_line}-{end_line}",
                    "content": chunk_content,
                    "start_line": start_line,
                    "end_line": end_line,
                }
            )

        return chunks