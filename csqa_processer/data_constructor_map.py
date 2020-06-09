# coding=utf-8
import codecs
import json
import re
import os


DATA_DIR_0 = "../../data/processed0/"
DATA_DIR_1 = "../../data/processed1/"
DATA_DIR_2 = "./out_dir/processed_test/"
QTYPE_DIR_TRAIN = "../../data/qtype_train/"
QTYPE_DIR_TEST = "./out_dir/qtype_test/"

RAW_DIR = "./CSQA_v9/"
TARG_DIR = "./CSQA_labeled/"

skipped = []
ENTITY_DIR = "./items_wikidata_n.json"
ENTITY_DIC = json.loads(codecs.open(ENTITY_DIR, "r", encoding="utf-8").read())

class Action(object):
	def __init__(self):
		self.action = "norewrite"
		self.pattern_rec = {"^(6-[23])|([78]-\\d-1)": "replace {before_ques} , {after}",
		"^3|(2-\\d-[23])|(5-[2356])|(7-[789]-0)|(8-([89]|10)-0)": "replace ref , {before_ans}", # 7和8里面的貌似被删掉了
		# "^3|(2-\\d-[23])|(5-[2356])": "replace(ref, {before_ans})", 
		"^9": "replace ref , {after}",
		"^4-1-1": "replace {before_ques} , or {before_ques} , {after}",
		"^4-2-1": "replace {before_ques} , and {before_ques} , {after}",
		"^4-3-1": "replace {before_ques} , not {before_ques} , {after}"}
		# "^6-1":


	def get_action(self, act_type):
		for p, a in self.pattern_rec.items():
			if re.match(p, act_type):
				self.action = a
				return a
		return self.action


def get_labeled_data(process_mode="train"):
	skipped_file = codecs.open("skipped.txt", mode="w", encoding="utf-8")
	if process_mode == "train":
		qtype_dir = QTYPE_DIR_TRAIN
		processed_files_0 = os.listdir(DATA_DIR_0) # 一次加载不了
		processed_files_1 = os.listdir(DATA_DIR_1)
		processed_files = processed_files_0 + processed_files_1
	else:
		qtype_dir = QTYPE_DIR_TEST
		processed_files = os.listdir(DATA_DIR_2)
	files = os.listdir(qtype_dir)


	pattern = "^1|(2-\\d-[14])|([78]-\\d-0)|(5-[14])"
	pattern_dis = "^(8-([89]|10)-0)|(7-[789]-0)|(6-1)"
	# pattern_tmp = "(7-[789]-0)|(8-([89]|10)-0)"
	res = ""
	for f in files:
		if re.match(pattern_dis, f):
			continue
		targ = codecs.open(TARG_DIR + f + "_" + process_mode + "_labeled.txt", mode="w", encoding="utf-8")
		if re.match(pattern, f):
			res = process(get_ques(f, qtype_dir), f, None, "raw", process_mode)
		else:
			res = process(get_ques(f, qtype_dir), f, processed_files, "processed", process_mode)
		targ.write(res)
		targ.write("\n")
		targ.close()
	skipped_file.write("\n".join(skipped))


def get_ques(data_file, qtype_dir):
	print(qtype_dir + data_file)
	fi = codecs.open(qtype_dir + data_file, encoding="utf-8", mode="r")
	#lines = fi.readlines()[:100]
	lines = fi.readlines()
	rec = dict()
	for l in lines:
		q, f = l.strip().split("\t")
		rec[f] = q
	fi.close()
	return rec



# 还是按qtype文件来，否则自己判断每个dial需要重新划分段落
def process(rec, act_type, processed_files, data_type="processed", process_mode="train"):
	act = Action()
	res = []
	for f, q in rec.items():
		tmp_act_type = act_type
		# entity_rec = dict()
		all_entities = dict()
		entity_rec = {}
		f = f[:f.find(".json")]
		find_q = False
		if data_type == "processed":
			for p in processed_files:
				if f in p:
					dial = load_data(p, data_type, process_mode)
					sens = [d["utterance"] for d in dial]
					if q in sens:
						raw_file = f
						raw_sens = q
						find_q = True
						break
		elif data_type == "raw":
			fs = f.split("-")
			file = fs[0] + "/" + fs[1] + ".json"
			dial = load_data(file, data_type, process_mode)
			sens = [d["utterance"] for d in dial]
			if q in sens:
				raw_file = f
				raw_sens = q
				find_q = True


		seq = []
		if not find_q:
			# print("not found", f, q)
			continue
		label = []
		for idx in range(len(dial)):
			turn = dial[idx]
			entities = []
			utter = turn["utterance"]
			processed_utter = utter.replace(", ", " , ").replace(". ", " . ").replace("? ", " ? ").replace("}?", "} ? ").strip()
			if "entity_list" in turn:
				entities = turn["entity_list"]
			elif data_type == "raw" and "entities_in_utterance" in turn:
				for e in turn["entities_in_utterance"]:
					# entities.append(ENTITY_DIC[e])
					span = ENTITY_DIC[e]
					tmp_idx = utter.find(span)
					if tmp_idx == -1:
						continue
					end_idx = tmp_idx + len(span)
					entities.append({"span": utter[tmp_idx: end_idx]})

			placeholder = ""
			if "No, I meant" in utter and not entities:
				tmp_idx = utter.find("No, I meant ")
				end_idx = utter.find(".", tmp_idx)
				entities.append({"span": utter[tmp_idx + 12: end_idx]})
			tmp_en = ""
			for e in range(len(entities)):
				ens = entities[e]
				# if not ens["span"] in entity_rec: 实体本身编号必要性不大
					# entity_rec[ens["span"]] = "entity" + str(len(entity_rec) + 1)
				# placeholder = "{}-{}.{}".format(entity_rec[ens["span"]], str(idx), str(e))
				placeholder = "entity{}.{}".format(str(idx), str(e))
				placeholder = "{" + placeholder + "}"
				
				processed_utter = processed_utter.replace(ens["span"], placeholder)
				entity_rec[placeholder] = ens["span"]
				tmp_en += placeholder + " "
			tmp_en = tmp_en.strip()
			# if len(entities) > 1:
				# all_entities[idx] = "{entity-" + str(idx) + "}"
			# elif placeholder:
			# 	all_entities[idx] = placeholder


			label_tmp = ["O"] * len(processed_utter.split())
			err_flag = False
			if "coref_mention" in turn:
				try:
					coref = turn["coref_mention"]
					coref_idx = processed_utter.find(coref)
					coref_idx = len(processed_utter[:coref_idx].split())
					label_tmp[coref_idx] = "B"
					for i in range(coref_idx + 1, coref_idx + len(coref.split())):
						label_tmp[i] = "I"
				except Exception as e:
					print(turn)
					print(coref)
					print(processed_utter)
					err_flag = True
			
			if err_flag:
				seq = []
				skipped.append(p)
				break
			if utter != q:
				label_tmp += "O"
			label += label_tmp

			all_entities[idx] = tmp_en
			seq.append(processed_utter)

			if utter == q:
				if "No, I meant" in utter: # type2 type8等里面都有这种，归为一类
					tmp_act_type = "9"

				length = len(all_entities)
				after = ""
				before_ans = ""
				before_ques = ""
				if idx in all_entities:
					after = all_entities[idx]
				if idx - 1 in all_entities:
					before_ans = all_entities[idx - 1]
				if idx - 2 in all_entities:
					before_ques = all_entities[idx - 2]
				ent_dict = {}
				if after:
					ent_dict["after"] = after
				if before_ques:
					ent_dict["before_ques"] = before_ques
					ent_dict["before_ans"] = before_ques
				if before_ans:
					ent_dict["before_ans"] = before_ans

				# 缺实体无法构成所需action的就跳过
				try:
					action = act.get_action(tmp_act_type).format(**ent_dict)
					seq.append(" || " + action + " || " + " ".join(label))
				except Exception as e:
					# print("#" * 50)
					# print(tmp_act_type)
					# print(p)
					# print(seq)
					# print(e)
					seq = []
					skipped.append(p)
				break
		if seq:
			res.append(raw_file + "\t" + raw_sens + "\t"+ str(entity_rec) + "\t" + " ; ".join(seq[:-1]) + seq[-1])
	return "\n".join(res)
	



def load_data(data_file, data_type="processed", process_mode="train"):
	if data_type == "processed":
		if process_mode == "train":
			dfile = DATA_DIR_0 + data_file
			if not os.path.isfile(dfile):
				dfile = DATA_DIR_1 + data_file
		elif process_mode == "test":
			dfile = DATA_DIR_2 + data_file
		data = json.loads(codecs.open(dfile, "r", encoding="utf-8").read())
	elif data_type == "raw":
		dfile = RAW_DIR + process_mode + "/" + data_file
		data = json.loads(codecs.open(dfile, "r", encoding="utf-8").read())
	# entities = data["entity_list"]
    # print(len(data))
    # print(data[0])
	return data


#get_labeled_data("train")
get_labeled_data("test")

# a = Action()
# print(a.get_action("8-10-0"))
# load_data("../../data/processed/QA_0-QA_0-0.json")
