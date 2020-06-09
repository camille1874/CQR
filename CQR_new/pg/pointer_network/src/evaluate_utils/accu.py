import os
import codecs

DIR_1 = "../decoded"
DIR_2 = "../reference"
decoded = os.listdir(DIR_1)
reference = os.listdir(DIR_2)
accus = codecs.open("accu_results.txt", mode="w", encoding="utf-8")

total = len(decoded)
overall_correct = 0
para_correct = 0
action_correct = 0

for sec in decoded:
    ref = sec.split("_")[0] + "_reference.txt"
    pred = codecs.open(DIR_1 + "/" + sec).readlines()[0]
    ref = codecs.open(DIR_2 + "/" + ref).readlines()[0]
    q = pred.split("||")[0]
    pred = pred.split("||")[1]
    ref = ref.split("||")[1]
    if pred == ref:
        overall_correct += 1
    #else:
    #    print(q)
    #    print(pred)
    #    print(ref)
    preds = pred.split()
    refs = ref.split()
    refs_para = [x for x in refs if ("{" in x or "ref" in x)]
    preds_para = [x for x in preds if ("{" in x or "ref" in x)]
    refs_action = [x for x in refs if x not in refs_para]
    preds_action = [x for x in preds if x not in preds_para]
    if refs_para == preds_para:
        para_correct += 1
    if refs_action == preds_action:
        action_correct += 1

overall_accu = overall_correct / total
para_accu = para_correct / total
action_accu = action_correct / total

accus.write("overall accuracy: " + str(overall_accu) + "\n")
accus.write("parameter accuracy: " + str(para_accu) + "\n")
accus.write("action accuracy: " + str(action_accu) + "\n")
    
