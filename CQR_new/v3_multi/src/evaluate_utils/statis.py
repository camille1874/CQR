import codecs
from scipy import stats
from scikit_posthocs import posthoc_nemenyi_friedman as nf
import numpy as np

cqr = codecs.open("bleu_static.txt").readlines()
s2s = codecs.open("bleu_static_s2s.txt").readlines()
pg = codecs.open("bleu_static_pg.txt").readlines()

matrix = []
cqr_res = []
s2s_res = []
pg_res = []

for i in range(199787):
    cqr_res.append(float(cqr[i].strip()))
    s2s_res.append(float(s2s[i].strip()))
    pg_res.append(float(pg[i].strip()))

matrix.append(cqr_res)
matrix.append(s2s_res)
matrix.append(pg_res)
matrix = np.array(matrix)

#print(stats.friedmanchisquare(cqr_res, s2s_res, pg_res))
print(nf(a.T))

