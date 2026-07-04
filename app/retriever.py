import os
import glob
import chromadb
from chromadb.utils import embedding_functions

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(BASE_DIR, "app", "corpus")
CHROMA_STORE_DIR = os.path.join(BASE_DIR, "chroma_store")
COLLECTION_NAME = "clinical_calculators"

# We use all-MiniLM-L6-v2 for local lightweight embeddings
EMBEDDING_FUNCTION = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def chunk_markdown_file(filepath: str) -> list[dict]:
    """
    Parses a markdown file and chunks it by paragraph, tracking section headers.
    Returns a list of dicts with keys: id, text, metadata.
    """
    filename = os.path.basename(filepath)
    doc_id = os.path.splitext(filename)[0]
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    current_title = ""
    current_section = ""
    chunks = []
    current_para = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            current_title = stripped[2:].strip()
        elif stripped.startswith("## "):
            # If we transition sections, save current paragraph first
            if current_para:
                para_text = "\n".join(current_para).strip()
                if para_text:
                    chunks.append({
                        "title": current_title,
                        "section": current_section,
                        "text": para_text
                    })
                current_para = []
            current_section = stripped[3:].strip()
        elif stripped == "":
            if current_para:
                para_text = "\n".join(current_para).strip()
                if para_text:
                    chunks.append({
                        "title": current_title,
                        "section": current_section,
                        "text": para_text
                    })
                current_para = []
        else:
            current_para.append(line.rstrip())
            
    if current_para:
        para_text = "\n".join(current_para).strip()
        if para_text:
            chunks.append({
                "title": current_title,
                "section": current_section,
                "text": para_text
            })
            
    # Format chunks for Chroma
    formatted_chunks = []
    for idx, chunk in enumerate(chunks):
        # We inject title and section context into the text itself to improve retrieval accuracy
        chunk_text = f"Calculator: {chunk['title']}\nSection: {chunk['section']}\nContent:\n{chunk['text']}"
        chunk_id = f"{doc_id}_chunk_{idx}"
        formatted_chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "metadata": {
                "source": filename,
                "calculator": chunk["title"],
                "section": chunk["section"]
            }
        })
        
    return formatted_chunks

class Retriever:
    def __init__(self, db_path: str = CHROMA_STORE_DIR, force_reindex: bool = False):
        self.client = chromadb.PersistentClient(path=db_path)
        
        if force_reindex:
            try:
                self.client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass
                
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=EMBEDDING_FUNCTION
        )
        
        # Index corpus if the collection is empty
        if self.collection.count() == 0:
            self.index_corpus()
            
    def index_corpus(self):
        """Loads and indexes all markdown files from the corpus directory."""
        search_pattern = os.path.join(CORPUS_DIR, "*.md")
        files = glob.glob(search_pattern)
        
        if not files:
            print(f"Warning: No markdown files found in corpus directory: {CORPUS_DIR}")
            return
            
        ids = []
        documents = []
        metadatas = []
        
        for filepath in files:
            chunks = chunk_markdown_file(filepath)
            for chunk in chunks:
                ids.append(chunk["id"])
                documents.append(chunk["text"])
                metadatas.append(chunk["metadata"])
                
        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"Indexed {len(ids)} chunks from {len(files)} files.")

    MAX_CHUNKS_PER_DOC = 2

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """
        Retrieves the top k chunks matching the query, capped at
        MAX_CHUNKS_PER_DOC chunks per source document so one calculator's
        doc cannot crowd every competing calculator out of the context window.
        """
        # ponytail: over-fetch then cap per doc — cheap diversity re-rank, MMR if this stops being enough
        results = self.collection.query(
            query_texts=[query],
            n_results=max(k * 3, k)
        )

        retrieved_chunks = []
        per_doc_counts = {}
        if results and results["ids"] and results["ids"][0]:
            for idx in range(len(results["ids"][0])):
                chunk_id = results["ids"][0][idx]
                doc_id = chunk_id.rsplit("_chunk_", 1)[0]
                if per_doc_counts.get(doc_id, 0) >= self.MAX_CHUNKS_PER_DOC:
                    continue
                per_doc_counts[doc_id] = per_doc_counts.get(doc_id, 0) + 1
                retrieved_chunks.append({
                    "id": chunk_id,
                    "text": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "distance": results["distances"][0][idx] if "distances" in results and results["distances"] else None
                })
                if len(retrieved_chunks) >= k:
                    break
        return retrieved_chunks

def embed_text(text: str):
    """Embed a single string with the same model the corpus uses (numpy vector)."""
    import numpy as np
    return np.array(EMBEDDING_FUNCTION([text])[0])


# Global helper function for ease of use
_global_retriever = None
# ponytail: plain dict cache, cleared when full; real LRU only if query
# cardinality ever grows past the golden suite's repeated 41 queries
_retrieve_cache: dict[tuple[str, int], list[dict]] = {}
_RETRIEVE_CACHE_MAX = 256


def retrieve(query: str, k: int = 3) -> list[dict]:
    global _global_retriever
    cache_key = (query, k)
    if cache_key in _retrieve_cache:
        return [dict(chunk) for chunk in _retrieve_cache[cache_key]]
    if _global_retriever is None:
        _global_retriever = Retriever()
    result = _global_retriever.retrieve(query, k=k)
    if len(_retrieve_cache) >= _RETRIEVE_CACHE_MAX:
        _retrieve_cache.clear()
    _retrieve_cache[cache_key] = [dict(chunk) for chunk in result]
    return result
