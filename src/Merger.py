#!/usr/bin/python3
"""
The script which reads the parallel text/ner files and pos/chunk tags the sentences and merges the four pieces of
 information into CoNLL 2003 format train/test/dev files.
"""
import spacy
from random import random
from pathlib import Path
from tqdm import tqdm
nlp = spacy.load('en_core_web_sm')

# ################ defining the output files ################
if not Path("tagged/").exists():
    Path("tagged/").mkdir()
train_result = Path("tagged/result.train").open("w")
train_lemma_result = Path("tagged/result.lemma.train").open("w")
test_result = Path("tagged/result.test").open("w")
test_lemma_result = Path("tagged/result.lemma.test").open("w")
valid_result = Path("tagged/result.valid").open("w")
valid_lemma_result = Path("tagged/result.lemma.valid").open("w")

xml_files = ["parsed/2757 Tagged Fergus_Naomi_AST3_ML.xml", "parsed/1112 Tagged_ML.xml", "parsed/Jameson vol.1-AST.xml",
             "parsed/27810-RB-SW_ML.xml"]

total_number_of_lines = sum([sum([1 for line in open(ff+".res.txt")]) for ff in xml_files])

data_split_sizes = [0.9, 0.05, 0.05]

test_size = int(total_number_of_lines * data_split_sizes[1])
valid_size = int(total_number_of_lines * data_split_sizes[2])
train_size = total_number_of_lines - test_size - valid_size

previous_tag = ""
not_annotated_count = 0.0
annotated_count = 0.0

NON_ANNOTATED_DROP_RATIO = 0.2

for parsing_txt_file_name in xml_files:
    for txt_line, ner_line in tqdm(zip(Path(parsing_txt_file_name + ".res.txt").open(),
                                       Path(parsing_txt_file_name + ".ner.txt").open())):
        # print(token.text,token.lemma_,token.pos_, token.tag_, token.dep_, token.shape_, token.is_alpha, token.is_stop)
        sel_random = random()
        all_ner_tags = list(set(ner_line.split()))
        natd = len(all_ner_tags) == 1 and all_ner_tags[0] == "O"
        if natd:
            not_annotated_count += 1.0
        else:
            annotated_count += 1.0
        if sel_random < data_split_sizes[0] and train_size > 0:
            model = train_result
            model_lemma = train_lemma_result
            train_size -= 1
            if natd and random() < NON_ANNOTATED_DROP_RATIO:
                continue
        elif (sel_random < data_split_sizes[0] + data_split_sizes[1] and valid_size > 0) or \
                (sel_random < data_split_sizes[0] and train_size == 0):
            model = valid_result
            model_lemma = valid_lemma_result
            valid_size -= 1
        elif test_size > 0:
            model = test_result
            model_lemma = test_lemma_result
            test_size -= 1
        elif valid_size > 0:
            model = valid_result
            model_lemma = valid_lemma_result
            valid_size -= 1
        elif train_size > 0:
            model = train_result
            model_lemma = train_lemma_result
            train_size -= 1
            if natd and random() < NON_ANNOTATED_DROP_RATIO:
                continue
        else:
            raise ValueError()

        doc = nlp(txt_line)
        for token, ner in zip(doc, ner_line.split()):
            txt, lemma, pos, tag = token.text, token.lemma_, token.pos_, token.tag_
            if pos == "PUNCT":
                tag = "PUNCT"
            if tag != previous_tag:
                previous_tag = tag
                tag = "B-" + tag
            else:
                tag = "I-" + tag
            # print(txt, lemma, pos, tag, ner)
            model.write("{} {} {} {}\n".format(txt, pos, tag, ner))
            model_lemma.write("{} {} {} {}\n".format(lemma, pos, tag, ner))
        model.write("\n")
        model_lemma.write("\n")
        previous_tag = ""

train_result.close()
train_lemma_result.close()
test_result.close()
test_lemma_result.close()
valid_result.close()
valid_lemma_result.close()
print("Not annotated count: {} ({:.3f})\tAnnotated count: {} ({:.3f})".format(
    not_annotated_count, not_annotated_count / (not_annotated_count + annotated_count), annotated_count,
    annotated_count / (not_annotated_count + annotated_count)))
