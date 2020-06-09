import numpy as np

def get_wer(hyps, refs):
    wer = [wer_score(h, r) for h, r in zip(hyps, refs)] 
    wer = np.mean(wer)
    return wer

def wer_score(hyp, ref, print_matrix=False):
    N = len(hyp)
    M = len(ref)
    L = np.zeros((N,M))
    for i in range(0, N):
        for j in range(0, M):
            if min(i,j) == 0:
                L[i,j] = max(i,j)
            else:
                deletion = L[i-1,j] + 1
                insertion = L[i,j-1] + 1
                sub = 1 if hyp[i] != ref[j] else 0
                substitution = L[i-1,j-1] + sub
                L[i,j] = min(deletion, min(insertion, substitution))
    return L[N-1, M-1] / M
