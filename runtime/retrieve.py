from runtime.expand import expand_topics

def retrieval_depth(pace):
    if pace == "slow":
        return 20
    if pace == "medium":
        return 12
    if pace == "fast":
        return 6
    return 10


def retrieve(collection, query_vec, pace, query_text):
    N = retrieval_depth(pace)

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=N
    )

    docs = results["documents"][0]

    # topic expansion
    subtopics = expand_topics(query_text)

    for sub in subtopics:
        sub_vec = query_vec  # reuse for simplicity
        sub_results = collection.query(
            query_embeddings=[sub_vec],
            n_results=3
        )
        docs += sub_results["documents"][0]

    return docs
