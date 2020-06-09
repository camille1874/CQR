# -*- coding: utf-8 -*-
#/usr/bin/python3
'''
Feb. 2019 by kyubyong park.
kbpark.linguist@gmail.com.
https://www.github.com/kyubyong/transformer.

Preprocess the iwslt 2016 datasets.
'''

import os
import errno
import sentencepiece as spm
import re
from hparams import Hparams
import logging
import codecs

logging.basicConfig(level=logging.INFO)

def prepro(hp):
    prepro_train1 = codecs.open("./new_data/prepro/train_convex_src.txt").readlines()
    prepro_train2 = codecs.open("./new_data/prepro/train_convex_targ_action.txt").readlines()
    prepro_dev1 = codecs.open("./new_data/prepro/dev_convex_src.txt").readlines()
    prepro_dev2 = codecs.open("./new_data/prepro/dev_convex_targ_action.txt").readlines()
    prepro_test1 = codecs.open("./new_data/prepro/test_convex_src.txt").readlines()
    prepro_test2 = codecs.open("./new_data/prepro/test_convex_targ_action.txt").readlines()

    os.makedirs("new_data/segmented", exist_ok=True)
    train = '--input=new_data/prepro/convex.txt --pad_id=0 --unk_id=1 \
             --bos_id=2 --eos_id=3\
             --model_prefix=new_data/segmented/bpe --vocab_size={} \
             --model_type=bpe'.format(hp.vocab_size)
    spm.SentencePieceTrainer.Train(train)

    logging.info("# Load trained bpe model")
    sp = spm.SentencePieceProcessor()
    sp.Load("new_data/segmented/bpe.model")

    logging.info("# Segment")
    def _segment_and_write(sents, fname):
        with open(fname, "w") as fout:
            for sent in sents:
                pieces = sp.EncodeAsPieces(sent)
                fout.write(" ".join(pieces) + "\n")

    _segment_and_write(prepro_train1, "new_data/segmented/train_convex_src.bpe")
    _segment_and_write(prepro_train2, "new_data/segmented/train_convex_targ_action.bpe")
    _segment_and_write(prepro_train1, "new_data/segmented/dev_convex_src.bpe")
    _segment_and_write(prepro_train2, "new_data/segmented/dev_convex_targ_action.bpe")
    _segment_and_write(prepro_test1, "new_data/segmented/test_convex_src.bpe")
    _segment_and_write(prepro_test2, "new_data/segmented/test_convex_targ_action.bpe")

    logging.info("Let's see how segmented data look like")
    print("train1:", open("new_data/segmented/train_convex_src.bpe",'r').readline())
    print("train2:", open("new_data/segmented/train_convex_targ_action.bpe", 'r').readline())
    print("test1:", open("new_data/segmented/test_convex_src.bpe", 'r').readline())

if __name__ == '__main__':
    hparams = Hparams()
    parser = hparams.parser
    hp = parser.parse_args()
    prepro(hp)
    logging.info("Done")
