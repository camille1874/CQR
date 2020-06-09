import os
import codecs
from bleu import compute_bleu
from rouge import rouge
from wer import get_wer

#DIR_1 = "../decoded"
#DIR_2 = "../reference"
#decoded = os.listdir(DIR_1)
#reference = os.listdir(DIR_2)

ratio = "record_all"
decoded = codecs.open("../../old_log/" + ratio + "/decode/dec.txt").readlines()
reference = codecs.open("../../old_log/" + ratio + "/decode/ref.txt").readlines()
test_file = "test_all_noaction.txt"
#record_file_rouge = codecs.open("rouge_" + ratio + ".txt", mode = "w", encoding="utf-8")
record_file_bleu = codecs.open("bleu_" + ratio + ".txt", mode = "w", encoding="utf-8")
#record_file_wer = codecs.open("warr_" + ratio + ".txt", mode = "w", encoding="utf-8")

#error = codecs.open("error_" + ratio + ".txt", mode = "w", encoding="utf-8")

decoded_final = []
reference_final = []

#f_new = codecs.open("test_all_noaction.txt", mode="w", encoding="utf-8")
#lines = codecs.open("test_all.txt").readlines()


def process(l):
    splits = l.split("||")
    splits = [x.strip() for x in splits]
    turn, action, label = splits
    labels = label.split()
    turns = turn.split()
    actions = action.split()
    rewrited = turn.split(";")[-1]
    try:
        if action == "norewrite":
            pass
        elif "B" in labels[-len(turn[turn.rfind(";"):].split()):]:
            idx = labels.index("B", len(labels) - len(turn[turn.rfind(";"):].split()))
            end_idx = idx
            while end_idx < len(labels) and labels[end_idx] != "O":
                end_idx += 1
            replace = actions[actions.index("ref") + 2:]
            replace = " ".join(replace)
            rewrited = " ".join(turns[:idx]) + " " + replace + " " + " ".join(turns[end_idx:])
            rewrited = rewrited.split(";")[-1]
        #else if action == "norewrite":
        #    rewrited = turn.split(";")[-1]
        elif "and" in action or "or" in action or "not" in action:
            before = " ".join(actions[actions.index("replace") + 1: actions.index(",")])
            after = " ".join(actions[actions.index(",") + 2:])
            token = actions[actions.index(",") + 1]
            candidates = turn.split(";")
            cand_idx = before.split(".")[0][7:]
            rewrited = candidates[int(cand_idx)].replace(before, 
                    before + " " + token + " " + after)
        elif "No , I meant" in turn:
            sens = turn.split(";")[-3]
            en_start_idx = sens.find("{")
            en_end_idx = sens.rfind("}")
            after = " ".join(actions[actions.index(",") + 1:])
            rewrited = sens.replace(sens[en_start_idx: en_end_idx + 1], after)
        elif turns[-1].strip() == "Yes":
            sens = turn.split(";")[-3]
            tmp_idx = len(turn[:turn.index(sens)].split())
            ref_start_idx = label.index("B", tmp_idx)
            ref_end_idx = ref_start_idx
            while ref_end_idx < len(labels) and labels[ref_end_idx] != "O":
                ref_end_idx += 1
            after = " ".join(actions[actions.index(",") + 1:])
            rewrited = " ".join(turns[:ref_start_idx]) + " " + after + " " + " ".join(turns[ref_end_idx:])
            rewrited = rewrited.split(";")[-1]
        else:
            before = " ".join(actions[actions.index("replace") + 1: actions.index(",")])
            after = " ".join(actions[actions.index(",") + 1:])
            candidates = turn.split(";")
            cand_idx = before.split(".")[0][7:]
            rewrited = candidates[int(cand_idx)].replace(before, after)
    except Exception as e:
        print(e)
        print(turn)
        print(action)
        print(label)
    
    return rewrited
    
test = codecs.open(test_file).readlines()
no_single_dec = []
no_single_ref = []
no_context_dec = []
no_context_ref = []
coref_dec = []
coref_ref = []
logical_dec = []
logical_ref = []
incomp_dec = []
incomp_ref = []



for idx, sec in enumerate(decoded[:199787]):
    #idx = sec.split("_")[0]
    #ref = idx + "_reference.txt"
    
    #pred = codecs.open(DIR_1 + "/" + sec).readlines()[0]
    #ref = codecs.open(DIR_2 + "/" + ref).readlines()[0]
    
    pred = sec.strip()
    ref = reference[idx].strip()    

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

    if "replace" in ref:
        if "ref" in ref:
            coref_ref.append(rewrited)
            if pred == ref:
                coref_dec.append(rewrited)
            else:
                coref_dec.append(raw_query)
        elif "and" in ref or "or" in ref or "not" in ref:
            logical_ref.append(rewrited)
            if pred == ref:
                logical_dec.append(rewrited)
            else:
                logical_dec.append(raw_query)
        else:
            incomp_ref.append(rewrited)
            if pred == ref:
                incomp_dec.append(rewrited)
            else:
                incomp_dec.append(raw_query)
    elif "norewrite" in ref:
        if len(raw.split("||")[0].split(";")) == 1:
            no_single_ref.append(rewrited)
            if pred == ref:
                no_single_dec.append(rewrited)
            else:
                no_single_dec.append(raw_query)
        else:
            no_context_ref.append(rewrited)
            if pred == ref:
                no_context_dec.append(rewrited)
            else:
                no_context_dec.append(raw_query)

bleu_no_single = codecs.open("bleu_no_single.txt", mode = "w", encoding="utf-8")
bleu_no_context = codecs.open("bleu_no_context.txt", mode = "w", encoding="utf-8")
bleu_coref = codecs.open("bleu_coref.txt", mode = "w", encoding="utf-8")
bleu_logical = codecs.open("bleu_logical.txt", mode = "w", encoding="utf-8")
bleu_incomp = codecs.open("bleu_incomp.txt", mode = "w", encoding="utf-8")

no_single = compute_bleu([[r.split()] for r in no_single_ref], [d.split() for d in no_single_dec])
bleu_no_single.write("total: " + str(len(no_single_ref)) + "\n")
bleu_no_single.write("bleu-avg: " + str(no_single[0]) + "\n")

no_context = compute_bleu([[r.split()] for r in no_context_ref], [d.split() for d in no_context_dec])
bleu_no_context.write("total: " + str(len(no_context_ref)) + "\n")
bleu_no_context.write("bleu-avg: " + str(no_context[0]) + "\n")

coref = compute_bleu([[r.split()] for r in coref_ref], [d.split() for d in coref_dec])
bleu_coref.write("total: " + str(len(coref_ref)) + "\n")
bleu_coref.write("bleu-avg: " + str(coref[0]) + "\n")

logical = compute_bleu([[r.split()] for r in logical_ref], [d.split() for d in logical_dec])
bleu_logical.write("total: " + str(len(logical_ref)) + "\n")
bleu_logical.write("bleu-avg: " + str(logical[0]) + "\n")

incomp = compute_bleu([[r.split()] for r in incomp_ref], [d.split() for d in incomp_dec])
bleu_incomp.write("total: " + str(len(incomp_ref)) + "\n")
bleu_incomp.write("bleu-avg: " + str(incomp[0]) + "\n")





bleu = compute_bleu([[r.split()] for r in reference_final], [d.split() for d in decoded_final])
#rouge_res = rouge(decoded_final, reference_final)
#for n, r in rouge_res.items():
#    record_file_rouge.write(n + ": " + str(r) + "\n")

#warr = 1 - get_wer(decoded_final, reference_final)
#record_file_wer.write("warr: " + str(warr) + "\n")

record_file_bleu.write("bleu-avg: " + str(bleu[0]) + "\n")
record_file_bleu.write("bleu-1: " + str(bleu[1][0]) + "\n")
record_file_bleu.write("bleu-2: " + str(bleu[1][1]) + "\n")
record_file_bleu.write("bleu-4: " + str(bleu[1][3]) + "\n")
