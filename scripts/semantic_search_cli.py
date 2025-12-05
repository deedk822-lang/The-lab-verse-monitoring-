#!/usr/bin/env python3
"""
Command-Line Interface for Semantic Search and RAG
Usage: python semantic_search_cli.py [command] [options]
"""

import sys
import os
import argparse
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.semantic_search_rag import (
    SemanticSearchService,
    RAGService,
    ContentClusteringService
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_documents(filepath: str) -> list:
    """Load documents from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_results(results: dict, output_path: str):
    """Save results to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to: {output_path}")


def cmd_index(args):
    """Index documents for search"""
    logger.info("Building search index...")

    # Load documents
    documents = load_documents(args.input)
    logger.info(f"Loaded {len(documents)} documents")

    # Initialize service
    service = SemanticSearchService(backend=args.backend)

    # Build index
    service.build_index(documents, text_field=args.text_field)

    # Save index
    if args.backend == "annoy" and service.search_index:
        index_path = args.output or "search_index.ann"
        service.search_index.save(index_path)
        logger.info(f"Index saved to: {index_path}")

    logger.info("✅ Indexing complete!")


def cmd_search(args):
    """Search indexed documents"""
    logger.info(f"Searching for: {args.query}")

    # Load documents
    documents = load_documents(args.input)

    # Initialize and build index
    service = SemanticSearchService()
    service.build_index(documents, text_field=args.text_field)

    # Search
    results = service.search(args.query, top_k=args.top_k)

    # Display results
    print("\n" + "=" * 70)
    print(f"SEARCH RESULTS FOR: {args.query}")
    print("=" * 70)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'Untitled')}")
        print(f"   Score: {result.get('similarity_score', 0):.3f}")
        print(f"   {result[args.text_field][:200]}...")

    # Save if requested
    if args.output:
        save_results({"query": args.query, "results": results}, args.output)


def cmd_rag(args):
    """Generate RAG response"""
    logger.info(f"Generating RAG response for: {args.query}")

    # Load documents
    documents = load_documents(args.input)

    # Initialize service
    service = RAGService()
    service.index_documents(documents, text_field=args.text_field)

    # Generate response
    result = service.generate_response(
        args.query,
        top_k=args.top_k,
        use_rerank=args.rerank,
        rerank_top_n=args.rerank_top_n
    )

    # Display response
    print("\n" + "=" * 70)
    print(f"QUERY: {args.query}")
    print("=" * 70)
    print(f"\nRESPONSE:")
    print(result['response'])

    if result.get('citations'):
        print(f"\n📚 CITATIONS ({len(result['citations'])}):")
        for i, cite in enumerate(result['citations'], 1):
            print(f"   {i}. \"{cite['text']}\" (docs: {cite['document_ids']})")

    if result.get('source_document_ids'):
        print(f"\n📄 SOURCE DOCUMENTS ({len(result['source_document_ids'])}):")
        for doc_id in result['source_document_ids']:
            doc = result['documents'][int(doc_id)]
            print(f"   - {doc['title']}")

    # Save if requested
    if args.output:
        save_results(result, args.output)


def cmd_cluster(args):
    """Cluster documents"""
    logger.info(f"Clustering documents into {args.n_clusters} clusters...")

    # Load documents
    documents = load_documents(args.input)

    # Initialize service
    service = ContentClusteringService()

    # Cluster
    result = service.cluster_documents(
        documents,
        n_clusters=args.n_clusters,
        text_field=args.text_field
    )

    # Display summary
    print("\n" + "=" * 70)
    print(f"CLUSTERING RESULTS")
    print("=" * 70)
    print(f"\nTotal Documents: {len(documents)}")
    print(f"Number of Clusters: {result['n_clusters']}")

    print(f"\nCLUSTER SIZES:")
    for cluster_id, size in sorted(result['cluster_sizes'].items()):
        keywords = ', '.join(result['cluster_keywords'][cluster_id][:5])
        print(f"   Cluster {cluster_id}: {size} documents")
        print(f"      Keywords: {keywords}")

    # Save if requested
    if args.output:
        save_results(result, args.output)
        logger.info(f"Results saved to: {args.output}")


def cmd_similar(args):
    """Find similar documents"""
    # Load documents
    documents = load_documents(args.input)

    # Initialize service
    service = SemanticSearchService()
    service.build_index(documents, text_field=args.text_field)

    # Find similar
    similar = service.find_similar(args.doc_id, top_k=args.top_k)

    # Display
    source_doc = documents[args.doc_id]
    print("\n" + "=" * 70)
    print(f"SIMILAR TO: {source_doc.get('title', 'Untitled')}")
    print("=" * 70)

    for i, doc in enumerate(similar, 1):
        print(f"\n{i}. {doc.get('title', 'Untitled')}")
        print(f"   Score: {doc.get('similarity_score', 0):.3f}")
        print(f"   {doc[args.text_field][:150]}...")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Semantic Search and RAG CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index documents
  python semantic_search_cli.py index documents.json --output index.ann

  # Search
  python semantic_search_cli.py search documents.json "machine learning" --top-k 5

  # RAG query
  python semantic_search_cli.py rag documents.json "What is machine learning?"

  # Cluster documents
  python semantic_search_cli.py cluster documents.json --n-clusters 5

  # Find similar documents
  python semantic_search_cli.py similar documents.json 0 --top-k 5
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Index command
    index_parser = subparsers.add_parser('index', help='Index documents')
    index_parser.add_argument('input', help='Input JSON file with documents')
    index_parser.add_argument('--output', help='Output index file')
    index_parser.add_argument('--backend', default='annoy', choices=['annoy', 'elasticsearch'])
    index_parser.add_argument('--text-field', default='text', help='Field containing text')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search documents')
    search_parser.add_argument('input', help='Input JSON file with documents')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--top-k', type=int, default=10, help='Number of results')
    search_parser.add_argument('--text-field', default='text')
    search_parser.add_argument('--output', help='Output JSON file')

    # RAG command
    rag_parser = subparsers.add_parser('rag', help='Generate RAG response')
    rag_parser.add_argument('input', help='Input JSON file with documents')
    rag_parser.add_argument('query', help='Query for RAG')
    rag_parser.add_argument('--top-k', type=int, default=10, help='Documents to retrieve')
    rag_parser.add_argument('--rerank', action='store_true', help='Use reranking')
    rag_parser.add_argument('--rerank-top-n', type=int, default=5, help='Documents after reranking')
    rag_parser.add_argument('--text-field', default='text')
    rag_parser.add_argument('--output', help='Output JSON file')

    # Cluster command
    cluster_parser = subparsers.add_parser('cluster', help='Cluster documents')
    cluster_parser.add_argument('input', help='Input JSON file with documents')
    cluster_parser.add_argument('--n-clusters', type=int, default=5, help='Number of clusters')
    cluster_parser.add_argument('--text-field', default='text')
    cluster_parser.add_argument('--output', help='Output JSON file')

    # Similar command
    similar_parser = subparsers.add_parser('similar', help='Find similar documents')
    similar_parser.add_argument('input', help='Input JSON file with documents')
    similar_parser.add_argument('doc_id', type=int, help='Document ID')
    similar_parser.add_argument('--top-k', type=int, default=10, help='Number of results')
    similar_parser.add_argument('--text-field', default='text')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    try:
        if args.command == 'index':
            cmd_index(args)
        elif args.command == 'search':
            cmd_search(args)
        elif args.command == 'rag':
            cmd_rag(args)
        elif args.command == 'cluster':
            cmd_cluster(args)
        elif args.command == 'similar':
            cmd_similar(args)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.command in ['search', 'rag', 'cluster']:
            logger.info("Hint: Make sure your JSON file has 'text' field or specify --text-field")
        sys.exit(1)


if __name__ == "__main__":
    main()
