from sentence_transformers import SentenceTransformer
from pathlib import Path
from app.tools.filesystem import read_file
import numpy as np
from app.config import WORKSPACE_ROOT
from app.context.chunking import PythonChunker

class SemanticRetriever:
    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        chunker=None,
    ):
        self.model = SentenceTransformer(model_name)
        self.chunker = chunker or PythonChunker()

    def _get_files(self, path: str) -> list[str]:
        search_path = (WORKSPACE_ROOT / path).resolve()

        try:
            search_path.relative_to(WORKSPACE_ROOT)
        except ValueError:
            return []

        files = [
            file
            for file in search_path.rglob("*.py")
            if "__pycache__" not in file.parts
        ]

        return [
            str(file.relative_to(WORKSPACE_ROOT))
            for file in files
        ]

    def _load_documents(self, files: list[str]) -> list[dict]:
        documents = []

        for path in files:
            result = read_file(path)

            if not result["success"]:
                continue

            chunks = self.chunker.chunk(
                path,
                result["content"],
            )

            documents.extend(chunks)

        return documents

    def _embed_documents(self, documents: list[dict]):
        if len(documents)>0:
            texts = [document["content"] for document in documents]

            embeddings = self.model.encode(
                    texts,
                    normalize_embeddings=True,
                )

            for document, embedding in zip(documents, embeddings):
                document["embedding"] = embedding
            return documents
        return []

    def _embed_query(self, query: str):
        if not query:
            raise ValueError("Query cannot be empty")

        return self.model.encode(
            query,
            normalize_embeddings=True,

        )

    def _rank_documents(
        self,
        documents: list[dict],
        query_embedding,
        top_k: int,
    ) -> list[dict]:
        results = []

        if len(documents)>0:
            for document in documents:
                score = np.dot(
                    query_embedding,
                    document["embedding"],
                )

                results.append({
                    "path": document["path"],
                    "score": score,
                    "source": "semantic",
                })

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k]

    def search(
        self,
        query: str,
        path: str = ".",
        top_k: int = 5,
    ) -> list[dict]:
        files = self._get_files(path)

        if not files:
            return []

        documents = self._load_documents(files)

        if not documents:
            return []

        documents = self._embed_documents(documents)
        query_embedding = self._embed_query(query)

        ranked = self._rank_documents(
        documents,
        query_embedding,
        len(documents),
)

        return self._deduplicate_by_path(
            ranked,
            top_k,
        )

    def _deduplicate_by_path(
    self,
    results: list[dict],
    top_k: int,
) -> list[dict]:
        seen = set()
        unique = []

        for result in results:
            path = result["path"]

            if path in seen:
                continue

            seen.add(path)
            unique.append(result)

            if len(unique) == top_k:
                break

        return unique
    
        
            
