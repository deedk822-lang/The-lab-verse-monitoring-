"""
Semantic Search and RAG Service for Vaal AI Empire
Combines Cohere embeddings with vector search for intelligent content discovery
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import cohere
import numpy as np

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Semantic search using Cohere embeddings and vector similarity
    Supports both Annoy (local) and Elasticsearch (production) backends
    """

    def __init__(
        self,
        cohere_key: Optional[str] = None,
        backend: str = "annoy",  # "annoy" or "elasticsearch"
        embedding_model: str = "embed-v4.0"
    ):
        """
        Initialize semantic search service

        Args:
            cohere_key: Cohere API key
            backend: Vector search backend ("annoy" or "elasticsearch")
            embedding_model: Cohere embedding model to use
        """
        self.cohere_key = cohere_key or os.getenv("COHERE_API_KEY")
        self.backend = backend
        self.embedding_model = embedding_model

        # Initialize Cohere
        if not self.cohere_key:
            raise ValueError("COHERE_API_KEY must be set to use SemanticSearchService")
        self.co = cohere.Client(self.cohere_key)
        self.available = True

        # Initialize backend
        self.search_index = None
        self.documents = []
        self.embeddings = None

    def embed_texts(
        self,
        texts: List[str],
        input_type: str = "search_document"
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of text strings to embed
            input_type: "search_document" or "search_query"

        Returns:
            Numpy array of embeddings
        """
        if not self.available:
            # Mock embeddings for testing
            return np.random.rand(len(texts), 1024)

        try:
            response = self.co.embed(
                texts=texts,
                model=self.embedding_model,
                input_type=input_type
            )
            return np.array(response.embeddings)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return np.random.rand(len(texts), 1024)

    def build_index(
        self,
        documents: List[Dict],
        text_field: str = "text"
    ):
        """
        Build search index from documents

        Args:
            documents: List of document dictionaries
            text_field: Field name containing text to embed
        """
        logger.info(f"Building search index for {len(documents)} documents...")

        self.documents = documents
        texts = [doc[text_field] for doc in documents]

        # Generate embeddings
        self.embeddings = self.embed_texts(texts, input_type="search_document")

        # Build Annoy index
        if self.backend == "annoy":
            self._build_annoy_index()
        else:
            logger.warning(f"Backend {self.backend} not yet implemented")

        logger.info("Search index built successfully")

    def _build_annoy_index(self):
        """Build Annoy index for fast nearest neighbor search"""
        try:
            from annoy import AnnoyIndex

            n_dims = self.embeddings.shape[1]
            self.search_index = AnnoyIndex(n_dims, 'angular')

            for i, embedding in enumerate(self.embeddings):
                self.search_index.add_item(i, embedding)

            self.search_index.build(10)  # 10 trees
            logger.info("Annoy index built with 10 trees")

        except ImportError:
            logger.warning("Annoy not installed - using brute force search")
            self.search_index = None

    def search(
        self,
        query: str,
        top_k: int = 10,
        include_distances: bool = True
    ) -> List[Dict]:
        """
        Search for documents similar to query

        Args:
            query: Search query string
            top_k: Number of results to return
            include_distances: Include similarity scores

        Returns:
            List of document dictionaries with scores
        """
        if not self.documents:
            logger.warning("No documents indexed")
            return []

        # Embed query
        query_embedding = self.embed_texts([query], input_type="search_query")[0]

        # Search
        if self.search_index:
            return self._search_annoy(query_embedding, top_k, include_distances)
        else:
            return self._search_brute_force(query_embedding, top_k, include_distances)

    def _search_annoy(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        include_distances: bool
    ) -> List[Dict]:
        """Search using Annoy index"""
        try:
            indices, distances = self.search_index.get_nns_by_vector(
                query_embedding,
                top_k,
                include_distances=True
            )

            results = []
            for idx, dist in zip(indices, distances):
                result = self.documents[idx].copy()
                if include_distances:
                    result['similarity_score'] = 1 - (dist**2 / 2)  # Convert to 0-1 similarity
                    result['distance'] = dist
                results.append(result)

            return results
        except Exception as e:
            logger.error(f"Annoy search error: {e}")
            return self._search_brute_force(query_embedding, top_k, include_distances)

    def _search_brute_force(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        include_distances: bool
    ) -> List[Dict]:
        """Fallback brute force search using cosine similarity"""
        # Compute cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            result = self.documents[idx].copy()
            if include_distances:
                result['similarity_score'] = float(similarities[idx])
            results.append(result)

        return results

    def find_similar(
        self,
        document_id: int,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find documents similar to an existing document

        Args:
            document_id: Index of document in the corpus
            top_k: Number of results to return

        Returns:
            List of similar documents
        """
        if not self.search_index or document_id >= len(self.documents):
            return []

        try:
            indices, distances = self.search_index.get_nns_by_item(
                document_id,
                top_k + 1,  # +1 to exclude the query document itself
                include_distances=True
            )

            results = []
            for idx, dist in zip(indices[1:], distances[1:]):  # Skip first (itself)
                result = self.documents[idx].copy()
                result['similarity_score'] = 1 - (dist**2 / 2)
                result['distance'] = dist
                results.append(result)

            return results
        except Exception as e:
            logger.error(f"Similar document search error: {e}")
            return []


class RAGService:
    """
    Retrieval-Augmented Generation service
    Combines semantic search with Cohere's Chat API for grounded responses
    """

    def __init__(
        self,
        cohere_key: Optional[str] = None,
        chat_model: str = "command-a-03-2025",
        rerank_model: str = "rerank-english-v3.0"
    ):
        """
        Initialize RAG service

        Args:
            cohere_key: Cohere API key
            chat_model: Cohere chat model to use
            rerank_model: Cohere rerank model to use
        """
        self.cohere_key = cohere_key or os.getenv("COHERE_API_KEY")
        self.chat_model = chat_model
        self.rerank_model = rerank_model

        # Initialize Cohere
        if not self.cohere_key:
            raise ValueError("COHERE_API_KEY must be set to use RAGService")
        self.co = cohere.Client(self.cohere_key)
        self.available = True

        # Initialize semantic search
        self.search_service = SemanticSearchService(cohere_key=cohere_key)

    def index_documents(self, documents: List[Dict], text_field: str = "text"):
        """Build search index from documents"""
        self.search_service.build_index(documents, text_field)

    def rerank_documents(
        self,
        query: str,
        documents: List[Dict],
        top_n: int = 10,
        text_field: str = "text"
    ) -> List[Dict]:
        """
        Rerank documents using Cohere's rerank model

        Args:
            query: User query
            documents: List of documents to rerank
            top_n: Number of top documents to return
            text_field: Field containing document text

        Returns:
            Reranked documents with scores
        """
        if not self.available or not documents:
            return documents[:top_n]

        try:
            # Extract texts
            texts = [doc[text_field] for doc in documents]

            # Rerank
            response = self.co.rerank(
                model=self.rerank_model,
                query=query,
                documents=texts,
                top_n=top_n,
                return_documents=True
            )

            # Reconstruct documents with rerank scores
            reranked = []
            for result in response.results:
                doc = documents[result.index].copy()
                doc['rerank_score'] = result.relevance_score
                reranked.append(doc)

            return reranked

        except Exception as e:
            logger.error(f"Rerank error: {e}")
            return documents[:top_n]

    def generate_response(
        self,
        query: str,
        top_k: int = 10,
        use_rerank: bool = True,
        rerank_top_n: int = 5
    ) -> Dict:
        """
        Generate a grounded response using RAG

        Args:
            query: User query
            top_k: Number of documents to retrieve
            use_rerank: Whether to rerank retrieved documents
            rerank_top_n: Number of top documents after reranking

        Returns:
            Dictionary with response, citations, and source documents
        """
        if not self.available:
            return {
                "response": f"[MOCK] Response to: {query}",
                "citations": [],
                "documents": [],
                "mock": True
            }

        # Step 1: Retrieve relevant documents
        retrieved_docs = self.search_service.search(query, top_k=top_k)

        if not retrieved_docs:
            return {
                "response": "I don't have enough information to answer that question.",
                "citations": [],
                "documents": []
            }

        # Step 2: Rerank (optional)
        if use_rerank:
            documents = self.rerank_documents(
                query,
                retrieved_docs,
                top_n=rerank_top_n,
                text_field="text"
            )
        else:
            documents = retrieved_docs[:rerank_top_n]

        # Step 3: Format documents for Chat API
        formatted_docs = []
        for i, doc in enumerate(documents):
            formatted_docs.append({
                "id": str(i),
                "text": doc.get("text", ""),
                "title": doc.get("title", f"Document {i}")
            })

        # Step 4: Generate response with Chat API
        try:
            response = self.co.chat(
                message=query,
                documents=formatted_docs,
                model=self.chat_model
            )

            # Extract citations
            source_documents = []
            for citation in response.citations:
                for doc_id in citation.document_ids:
                    if doc_id not in source_documents:
                        source_documents.append(doc_id)

            return {
                "response": response.text,
                "citations": [
                    {
                        "text": cite.text,
                        "start": cite.start,
                        "end": cite.end,
                        "document_ids": cite.document_ids
                    }
                    for cite in response.citations
                ],
                "documents": formatted_docs,
                "source_document_ids": source_documents,
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Chat API error: {e}")
            return {
                "response": "Error generating response",
                "error": str(e),
                "citations": [],
                "documents": formatted_docs
            }

    def hybrid_search_rag(
        self,
        query: str,
        top_k: int = 50,
        rerank_top_n: int = 10
    ) -> Dict:
        """
        Perform hybrid search (semantic + keyword) with RAG

        This is a simplified version - full implementation would integrate
        with Elasticsearch for true hybrid search
        """
        # For now, just use semantic search
        return self.generate_response(
            query,
            top_k=top_k,
            use_rerank=True,
            rerank_top_n=rerank_top_n
        )


class ContentClusteringService:
    """
    Content clustering using Cohere embeddings and K-Means
    Useful for organizing large content libraries
    """

    def __init__(self, cohere_key: Optional[str] = None):
        """Initialize clustering service"""
        self.search_service = SemanticSearchService(cohere_key=cohere_key)
        self.clusters = None
        self.cluster_keywords = None

    def cluster_documents(
        self,
        documents: List[Dict],
        n_clusters: int = 8,
        text_field: str = "text"
    ) -> Dict:
        """
        Cluster documents into topics

        Args:
            documents: List of documents to cluster
            n_clusters: Number of clusters
            text_field: Field containing text

        Returns:
            Dictionary with cluster assignments and keywords
        """
        from sklearn.cluster import KMeans

        logger.info(f"Clustering {len(documents)} documents into {n_clusters} clusters...")

        # Get embeddings
        texts = [doc[text_field] for doc in documents]
        embeddings = self.search_service.embed_texts(texts)

        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.clusters = kmeans.fit_predict(embeddings)

        # Extract keywords per cluster
        self.cluster_keywords = self._extract_cluster_keywords(
            documents,
            self.clusters,
            text_field
        )

        # Add cluster info to documents
        clustered_docs = []
        for i, doc in enumerate(documents):
            doc_copy = doc.copy()
            doc_copy['cluster'] = int(self.clusters[i])
            doc_copy['cluster_keywords'] = self.cluster_keywords[self.clusters[i]]
            clustered_docs.append(doc_copy)

        return {
            "documents": clustered_docs,
            "n_clusters": n_clusters,
            "cluster_keywords": self.cluster_keywords,
            "cluster_sizes": {
                int(i): int(np.sum(self.clusters == i))
                for i in range(n_clusters)
            }
        }

    def _extract_cluster_keywords(
        self,
        documents: List[Dict],
        clusters: np.ndarray,
        text_field: str,
        top_n: int = 10
    ) -> Dict[int, List[str]]:
        """Extract top keywords for each cluster"""
        from sklearn.feature_extraction.text import CountVectorizer

        try:
            # Group documents by cluster
            cluster_texts = {}
            for i, doc in enumerate(documents):
                cluster_id = int(clusters[i])
                if cluster_id not in cluster_texts:
                    cluster_texts[cluster_id] = []
                cluster_texts[cluster_id].append(doc[text_field])

            # Extract keywords
            keywords = {}
            vectorizer = CountVectorizer(
                max_features=100,
                stop_words='english'
            )

            for cluster_id, texts in cluster_texts.items():
                combined_text = ' '.join(texts)
                try:
                    counts = vectorizer.fit_transform([combined_text])
                    feature_names = vectorizer.get_feature_names_out()
                    scores = counts.toarray()[0]
                    top_indices = np.argsort(scores)[-top_n:][::-1]
                    keywords[cluster_id] = [feature_names[i] for i in top_indices]
                except ValueError:
                    keywords[cluster_id] = [f"cluster_{cluster_id}"]

            return keywords

        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return {i: [f"cluster_{i}"] for i in range(len(set(clusters)))}

    def visualize_clusters(
        self,
        documents: List[Dict],
        text_field: str = "text"
    ) -> Dict:
        """
        Prepare data for cluster visualization using UMAP

        Returns:
            Dictionary with 2D coordinates and cluster info
        """
        try:
            import umap

            # Get embeddings
            texts = [doc[text_field] for doc in documents]
            embeddings = self.search_service.embed_texts(texts)

            # Reduce to 2D
            reducer = umap.UMAP(n_neighbors=100, random_state=42)
            coords_2d = reducer.fit_transform(embeddings)

            # Add coordinates to documents
            viz_data = []
            for i, doc in enumerate(documents):
                viz_data.append({
                    **doc,
                    'x': float(coords_2d[i, 0]),
                    'y': float(coords_2d[i, 1]),
                    'cluster': int(self.clusters[i]) if self.clusters is not None else 0
                })

            return {
                "documents": viz_data,
                "success": True
            }

        except ImportError:
            logger.warning("UMAP not installed - visualization not available")
            return {
                "documents": documents,
                "success": False,
                "error": "UMAP not installed"
            }
