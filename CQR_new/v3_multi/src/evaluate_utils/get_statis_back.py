import os
import codecs
from rouge import rouge
from wer import get_wer
from bleu import compute_bleu
from scipy import stats
from nltk.translate import bleu_score
from scipy import stats


test_file = "test_all_noaction.txt"

dir_cqr = "/home/xuzh/new/v3_multi/log/0.001/decode_test_25maxenc_3beam_1mindec_1maxdec_ckpt-4186/"
decoded = os.listdir(dir_cqr + "decoded")
reference = os.listdir(dir_cqr + "reference")
record_file = codecs.open("bleu_static.txt", mode = "w", encoding="utf-8")

dir_pg = "/home/xuzh/new/pg/pointer_network/log/0.001_old/decode_test_75maxenc_3beam_1mindec_1maxdec_ckpt-7606/"
decoded_pg = os.listdir(dir_pg + "decoded")
reference_pg = os.listdir(dir_pg + "reference")
record_file_pg = codecs.open("bleu_static_pg.txt", mode = "w", encoding="utf-8")

dir_s2s = "/home/xuzh/new/raw/pointer_network/log/0.01/decode_test_75maxenc_3beam_1mindec_1maxdec_ckpt-20728/"
decoded_s2s = os.listdir(dir_s2s + "decoded")
reference_s2s = os.listdir(dir_s2s + "reference")
record_file_s2s = codecs.open("bleu_static_s2s.txt", mode = "w", encoding="utf-8")



decoded_final = []
reference_final = []

decoded_final_s2s = []
reference_final_s2s = []

decoded_final_pg = []
reference_final_pg = []

    
test = codecs.open(test_file).readlines()



for sec in decoded:
    idx = sec.split("_")[0]
    ref = idx + "_reference.txt"

    pred = codecs.open(dir_cqr + "decoded/" + sec).readlines()[0]
    ref = codecs.open(dir_cqr + "reference/" + ref).readlines()[0]    
    q = pred.split("||")[0]
    pred = pred.split("||")[1]
    ref = ref.split("||")[1]
    raw = test[int(idx)]
    #pred = process(raw, pred)
    #ref = process(raw, ref)
    #rewrited = process(raw)
    rewrited = raw.split("||")[1].strip()
    reference_final.append(rewrited)
    raw_query = raw.split("||")[0].split(";")[-1].strip()
    if pred == ref:
        decoded_final.append(rewrited)
    else:
        #error.write(str(idx) + " " + pred + "--" + ref + "\n")
        decoded_final.append(raw_query)


for sec in decoded_s2s:
    idx = sec.split("_")[0]
    #if int(idx) >= 199787:
    #    continue
    ref = idx + "_reference.txt"
    pred = codecs.open(dir_s2s + "decoded/" + sec).readlines()[0]
    ref = codecs.open(dir_s2s + "reference/" + ref).readlines()[0]
    q = pred.split("||")[0]
    pred = pred.split("||")[1].strip()
    ref = ref.split("||")[1].strip()
    reference_final_s2s.append(ref)
    decoded_final_s2s.append(pred)


for sec in decoded_pg:
    idx = sec.split("_")[0]
    #if int(idx) >= 199787:
    #    continue
    ref = idx + "_reference.txt"
    pred = codecs.open(dir_pg + "decoded/" + sec).readlines()[0]
    ref = codecs.open(dir_pg + "reference/" + ref).readlines()[0]
    q = pred.split("||")[0]
    pred = pred.split("||")[1].strip()
    ref = ref.split("||")[1].strip()
    reference_final_pg.append(ref)
    decoded_final_pg.append(pred)


bleu_s2s = []
for r, d in zip(reference_final_s2s, decoded_final_s2s):
    t = bleu_score.sentence_bleu([r.split()], d.split())
    record_file_s2s.write(str(t) + "\n")
    bleu_s2s.append(t)
print("s2s_bleu_single")
print(sum(bleu_s2s) / len(bleu_s2s))
bleu_total_s2s = compute_bleu([[r.split()] for r in reference_final_s2s], [d.split() for d in decoded_final_s2s])
print("s2s_bleu_total")
print(bleu_total_s2s)


bleu_pg = []
for r, d in zip(reference_final_pg, decoded_final_pg):
    t = bleu_score.sentence_bleu([r.split()], d.split())
    record_file_pg.write(str(t) + "\n")
    bleu_pg.append(t)
print("pg_bleu_single")
print(sum(bleu_pg) / len(bleu_pg))
bleu_total_pg = compute_bleu([[r.split()] for r in reference_final_pg], [d.split() for d in decoded_final_pg])
print("pg_bleu_total")
print(bleu_total_pg)


bleu = []
for r, d in zip(reference_final, decoded_final):
    t = bleu_score.sentence_bleu([r.split()], d.split())
    record_file.write(str(t) + "\n")
    bleu.append(t)
print("cqr_bleu_single")
print(sum(bleu) / len(bleu))
bleu_total = compute_bleu([[r.split()] for r in reference_final], [d.split() for d in decoded_final])
print("cqr_bleu_total")
print(bleu_total)


print("stas:")
print(stats.friedmanchisquare(bleu_s2s, bleu_pg, bleu))
