import os
import codecs

decoded = codecs.open("../../log/convex/decode/dec.txt").readlines()[:6712]
reference = codecs.open("../../log/convex/decode/ref.txt").readlines()[:6712]
#decoded = codecs.open("../../convex_log/exp/decode/dec.txt").readlines()[:6712]
#reference = codecs.open("../../convex_log/exp/decode/ref.txt").readlines()[:6712]
accus = codecs.open("accu_results.txt", mode="w", encoding="utf-8")

total = len(decoded)
overall_correct = 0
para_correct = 0
action_correct = 0

for pred, ref in zip(decoded, reference):
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
    
