#!/usr/bin/env python3
"""
Build a FAISS index locally from visits.json and optionally upload artifacts to Supabase Storage.

Outputs:
- index.faiss
- vectors.npy
- metadata.json

Optional upload env (server-side):
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_BUCKET (default: web-memory)
"""
import os
import json
import argparse
import numpy as np


def load_visits(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_docs(visits):
    session_docs = []
    page_docs = []
    for s in visits:
        pages = s.get('pages', [])
        combined = []
        for p in pages:
            title = p.get('title') or ''
            snippet = p.get('snippet') or ''
            url = p.get('url') or ''
            combined.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}")
            page_docs.append({
                'id': f"page:{s['id']}:{p.get('ts', 0)}",
                'title': title,
                'url': url,
                'snippet': snippet,
                'sessionId': s['id'],
                'start': s.get('start'),
                'end': s.get('end')
            })
        session_docs.append({
            'id': f"session:{s['id']}",
            'title': s.get('sessionTitle') or (pages[0]['title'] if pages else f"Session {s['id']}") ,
            'text': "\n\n".join(combined),
            'sessionId': s['id'],
            'start': s.get('start'),
            'end': s.get('end')
        })
    return session_docs, page_docs


def build_embeddings(texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim
    emb = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    emb = np.asarray(emb, dtype=np.float32)
    return emb


def build_faiss(emb):
    import faiss
    faiss.normalize_L2(emb)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    return index


def save_artifacts(index, emb, session_docs, page_docs, out_dir: str):
    import faiss
    os.makedirs(out_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(out_dir, 'index.faiss'))
    np.save(os.path.join(out_dir, 'vectors.npy'), emb)
    with open(os.path.join(out_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
        json.dump({'sessions': session_docs, 'pages': page_docs}, f, ensure_ascii=False, indent=2)


def maybe_upload(out_dir: str):
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    bucket = os.getenv('SUPABASE_BUCKET', 'web-memory')
    if not url or not key:
        print('Skip upload (set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to upload)')
        return
    import requests
    for name, ctype in [
        ('index.faiss', 'application/octet-stream'),
        ('vectors.npy', 'application/octet-stream'),
        ('metadata.json', 'application/json'),
    ]:
        path = os.path.join(out_dir, name)
        with open(path, 'rb') as f:
            r = requests.post(
                f"{url}/storage/v1/object/{bucket}/{name}",
                headers={
                    'Authorization': f'Bearer {key}',
                    'Content-Type': ctype,
                },
                data=f,
                timeout=60,
            )
        print(name, r.status_code, r.text[:100])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('visits', help='path to visits.json')
    ap.add_argument('--out', default='faiss_out', help='output directory')
    args = ap.parse_args()

    visits = load_visits(args.visits)
    print(f"Loaded {len(visits)} sessions from {args.visits}")

    session_docs, page_docs = build_docs(visits)
    texts = [s['text'] for s in session_docs]
    emb = build_embeddings(texts)
    index = build_faiss(emb)
    save_artifacts(index, emb, session_docs, page_docs, args.out)
    print('Artifacts written to', args.out)
    maybe_upload(args.out)


if __name__ == '__main__':
    main()
