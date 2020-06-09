import os
import codecs
from bleu import compute_bleu
from rouge import rouge
from wer import get_wer

#DIR_1 = "../decoded"
#DIR_2 = "../reference"
#decoded = os.listdir(DIR_1)
#reference = os.listdir(DIR_2)
#test_file = "test_all_noaction.txt"
#record_file_rouge = codecs.open("rouge.txt", mode = "w", encoding="utf-8")
record_file_bleu = codecs.open("bleu.txt", mode = "w", encoding="utf-8")
#record_file_wer = codecs.open("warr.txt", mode = "w", encoding="utf-8")

#error = codecs.open("error.txt", mode = "w", encoding="utf-8")


#ratio = "all"
#decoded = codecs.open("../../log/exp/decode/dec.txt").readlines()
#reference = codecs.open("../../log/exp/decode/ref.txt").readlines()
decoded = codecs.open("../../log/csqa/decode/dec.txt").readlines()
reference = codecs.open("../../log/csqa/decode/ref.txt").readlines()

tmp = []
idx_ref = 0
for d in decoded:
    if d.split("||")[0] != reference[idx_ref].split("||")[0]:
        continue
    else:
        idx_ref += 1
        if idx_ref >= len(reference):
            break
        tmp.append(d)	
decoded = tmp
print(len(decoded))

#classify = codecs.open("all_test.txt").readlines()

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
    
#test = codecs.open(test_file).readlines()

for idx, sec in enumerate(decoded):
    #idx = sec.split("_")[0]
    #if int(idx) >= 199787:
    #    continue
    #ref = idx + "_reference.txt"

    #pred = codecs.open(DIR_1 + "/" + sec).readlines()[0]
    #ref = codecs.open(DIR_2 + "/" + ref).readlines()[0]
    
    pred = sec.strip()
    ref = reference[idx].strip()
    
    q = pred.split("||")[0]
    pred = pred.split("||")[1].strip()
    ref = ref.split("||")[1].strip()
    decoded_final.append(pred)
    reference_final.append(ref)



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
