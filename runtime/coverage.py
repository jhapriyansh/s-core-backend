from sentence_transformers import util

def coverage_check(docs, query_vec, embed_fn):
    sims = []
    for d in docs:
        dv = embed_fn(d)
        sim = util.cos_sim(query_vec, dv)[0][0].item()
        sims.append(sim)

    # if nothing is semantically close to query
    if max(sims) < 0.25:
        return False
    return True
