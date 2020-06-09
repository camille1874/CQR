import codecs
import re
import os
import json
rewrite_lines = codecs.open("map_file.txt").readlines()
CSQA_DIR = "./CSQA_labeled/"
error = codecs.open("error.txt", mode="w", encoding="utf-8")
#CSQA_DIR_NEW = "./CSQA_test/"
CSQA_DIR_NEW = "./CSQA_test_w_clarification/"
ENTITY_DIR = "./items_wikidata_n.json"


entity_dic = json.loads(codecs.open(ENTITY_DIR, "r", encoding="utf-8").read())
entity_dic_reverse = {v:k for k, v in entity_dic.items()}

type_map = os.listdir(CSQA_DIR)
pattern_rec = {
"replace {entity\\d+\\.\\d+} , {entity\\d+\\.\\d+}": "^(6-[23])|([78]-\\d-1)",
"replace ref , {entity\\d+\\.\\d+}": "^[39]|(2-\\d-[23])|(5-[2356])",
"replace {entity\\d+\\.\\d+} , or {entity\\d+\\.\\d+} , {entity\\d+\\.\\d+}": "^4-1-1", 
"replace {entity\\d+\\.\\d+} , and {entity\\d+\\.\\d+} , {entity\\d+\\.\\d+}": "^4-2-1", 
"replace {entity\\d+\\.\\d+} , not {entity\\d+\\.\\d+} , {entity\\d+\\.\\d+}": "^4-3-1"
}

def update(raw_csqa, raw_dialog, rewrited, ent_dic):
	#print(raw_csqa)
	items = raw_csqa.split("-")
	dir_name = items[0]
	file_name = items[1]
	raw_name = CSQA_DIR_NEW + "/" + dir_name + "/" + file_name + ".json"
	raw_file = open(raw_name, 'r+', encoding='utf-8')
	js = json.loads(raw_file.read())
	for turn in range(len(js)):
		if js[turn]["utterance"] == raw_dialog:
			if js[turn]["ques_type_id"] == 3 or (not "entities_in_utterance" in js[turn]):
				break
			#if not "entities_in_utterance" in js[turn]:
			#	js[turn]["utterance"] = rewrited
			#	#js[turn]["entities_in_utterance"] = [entity_dic_reverse[e] for e in ent_dic.values()]
			#	new_ens = []
			#	for e in ent_dic.values():
			#		if e in entity_dic_reverse:
			#			new_ens.append(entity_dic_reverse[e])
			#	js[turn]["entities_in_utterance"] = new_ens
			else:
				for entity in js[turn]["entities_in_utterance"]:
					if not entity_dic[entity] in rewrited:
						break
				else:
					js[turn]["utterance"] = rewrited
					#print(js[turn])
			#print(js[turn]["utterance"])
			#print(rewrited)
			break
	raw_file.seek(0)
	raw_file.truncate()
	json.dump(js, raw_file, indent=1)


for line in rewrite_lines:
	raw_csqa = ""
	dialog, raw_action, rewrited = line.strip().split(" || ")
	if raw_action == "norewrite":
		continue
	for p, f in pattern_rec.items():
		if re.match(p, raw_action):
			file_pattern = f
			for tm in type_map:
				if re.match(file_pattern, tm):
					lines = codecs.open(CSQA_DIR + tm, encoding="utf-8").readlines()
					for l in lines:
						items = l.split("\t")
						sample = items[-1].split("||")[0].strip()
						if sample == dialog or sample == dialog.replace(" ?", "?"):
							raw_csqa = items[0].strip()
							raw_dialog = items[1].strip()
							ent_dic = eval(items[2])
							words = rewrited.split()
							for word in words:
								if word in ent_dic:
									rewrited = rewrited.replace(word, ent_dic[word])
							update(raw_csqa, raw_dialog, rewrited, ent_dic)
							break
				if raw_csqa:
					break
		if raw_csqa:
			break
			
	if not raw_csqa:
		error.write(line)
