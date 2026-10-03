import math
import re
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Sample corpus - imagine these are your Django docs
docs = [
    "How to scale django with gunicorn and nginx",
    "Django deployment tutorial gunicorn nginx scaling",
    "Python basics for beginners",
    "Scaling python web applications with kubernetes and django",
    "How to deploy django application to production"
]

def tokenize(text):
    return re.findall(r'\w+', text.lower())

res =[tokenize(d) for d in docs]
print(res)
avgdl = sum(len(d) for d in docs) / len(docs)
print(avgdl)
doc_len = [len(d) for d in docs]
print(doc_len)

# Document Frequency df(t)
df = Counter()
for doc in res:
    df.update(set(doc))
print(df)

 # IDF per term
idf = {}
for term, freq in df.items():
    # BM25 IDF formula with smoothing to avoid negative
    idf[term] = math.log(1 + (len(docs) - freq + 0.5) / (freq + 0.5))
print(idf)


# --- CORE BM25 CLASS ---
class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.docs = [tokenize(d) for d in docs]
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / self.N
        self.doc_len = [len(d) for d in self.docs]

        # Document Frequency df(t)
        self.df = Counter()
        for doc in self.docs:
            self.df.update(set(doc))

        # IDF per term
        self.idf = {}
        for term, freq in self.df.items():
            # BM25 IDF formula with smoothing to avoid negative
            self.idf[term] = math.log(1 + (self.N - freq + 0.5) / (freq + 0.5))

    def score(self, query: str):
        q_terms = tokenize(query)
        scores = np.zeros(self.N)

        for doc_idx, doc in enumerate(self.docs):
            tf = Counter(doc)
            print('tf:',tf)
            doc_score = 0
            for term in q_terms:
                if term not in self.idf:
                    continue
                # TF component with saturation + length norm
                tf_term = tf[term]
                print(tf_term)
                numerator = tf_term * (self.k1 + 1)
                denominator = tf_term + self.k1 * (1 - self.b + self.b * self.doc_len[doc_idx] / self.avgdl)

                doc_score += self.idf[term] * (numerator / denominator)
            scores[doc_idx] = doc_score
        return scores

# --- RUN & COMPARE ---
query = "how to scale django deployment"

bm25 = BM25(docs)
bm25_scores = bm25.score(query)

# TF-IDF from sklearn (does TF_log + IDF + L2 norm)
vectorizer = TfidfVectorizer(tokenizer=tokenize, lowercase=False)
tfidf_matrix = vectorizer.fit_transform(docs)
print(f"tfidf_matrix: {tfidf_matrix}")
query_vec = vectorizer.transform([query])
print(f"query_vec: {query_vec}")
tfidf_scores = (tfidf_matrix @ query_vec.T).toarray().ravel()
print(f"tfidf_scores:{tfidf_scores}")

print(f"Query: '{query}'\n")
for i, doc in enumerate(docs):
    print(f"Doc {i}: {doc}")
    print(f" -> BM25: {bm25_scores[i]:.3f} | TF-IDF: {tfidf_scores[i]:.3f}")
    print()

# Rank
print("BM25 Ranking:", np.argsort(-bm25_scores))
print("TF-IDF Ranking:", np.argsort(-tfidf_scores))