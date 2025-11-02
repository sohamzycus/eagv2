#!/usr/bin/env python3
"""
FAISS CLI search over local artifacts produced by build_faiss_local.py

Usage:
  python tools/search_faiss_local.py --index faiss_out/index.faiss --vectors faiss_out/vectors.npy --meta faiss_out/metadata.json --k 5 --query "vector search in postgres"

Requires:
  - sentence-transformers, faiss-cpu, numpy
"""
import argparse
import json
import numpy as np


def load_faiss(index_path):
    import faiss
    index = faiss.read_index(index_path)
    return index


def embed_query(text: str):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim
    q = model.encode([text], normalize_embeddings=True)
    return np.asarray(q, dtype=np.float32)


def search(index, qvec, k):
    import faiss
    # index was built on normalized vectors; normalize query too
    faiss.normalize_L2(qvec)
    D, I = index.search(qvec, k)
    return D[0], I[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', default='faiss_out/index.faiss')
    ap.add_argument('--vectors', default='faiss_out/vectors.npy')
    ap.add_argument('--meta', default='faiss_out/metadata.json')
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--query', required=True)
    args = ap.parse_args()

    index = load_faiss(args.index)
    q = embed_query(args.query)
    D, I = search(index, q, args.k)

    # Load metadata to print titles/ids
    with open(args.meta, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    sessions = meta.get('sessions', [])

    print(f"\nTop {args.k} results for: {args.query}\n")
    for rank, (score, idx) in enumerate(zip(D, I), start=1):
        if idx < 0 or idx >= len(sessions):
            continue
        s = sessions[idx]
        title = s.get('title') or s.get('id')
        sid = s.get('id')
        print(f"{rank}. {title}  (session={sid})  similarity={float(score):.4f}")


if __name__ == '__main__':
    main()
