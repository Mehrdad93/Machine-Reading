#!/usr/bin/python3
"""
This is the script to read the TEI-formatted xml files of the books and parse them into two parallel files in a one 
 sentence per line format (the lines are extracted using a heuristic). One file will contain the actual sentences and 
  the other will contain the sequence of their NER tags
"""
import xml.sax
from collections import Counter

from pathlib import Path


class TEISAXHandler(xml.sax.ContentHandler):
    def __init__(self, content_file_name):
        self.inside_body = False
        self.inside_p = False
        self.inside_preface = False
        self.page_break_has_just_happened = False
        self.traverse_stack = []
        self.content_file_name = content_file_name
        cfn = content_file_name.split("/")[-1]
        if not Path("parsed/").exists():
            Path("parsed/").mkdir()
        self.text_result_file = Path("parsed/" + cfn + ".res.txt").open("w")
        self.ner_result_file = Path("parsed/" + cfn + ".ner.txt").open("w")
        self.text_buffer = []
        self.ner_buffer = []
        self.persons_count = 0.0
        self.outsiders_count = 0.0
        self.tags_of_interest = Counter({"persName": 0.0,
                                         "date": 0.0, "placeName": 0.0, "roleName": 0.0,
                                         # # we need only trait[type:ethnicity].label rather than label and
                                         # # trait try to label it "ethnicity"
                                         # "trait[type:ethnicity]": 0.0, "label": 0.0,
                                         "trait[type:ethnicity].label": 0.0,
                                         "trait[type:race].label": 0.0,
                                         "trait[type:religion].label": 0.0,
                                         "date.persName": 0.0,
                                         "roleName.persName": 0.0,
                                         "roleName.placeName": 0.0,
                                         "roleName.orgName": 0.0,
                                         "orgName": 0.0,
                                         "orgName.orgName": 0.0,
                                         "persName.roleName": 0.0,
                                         "trait[type:ethnicity].label.roleName": 0.0,
                                         "roleName.trait[type:religion].label": 0.0,
                                         "trait[type:ethnicity].label.placeName": 0.0,
                                         "trait[type:religion].label.roleName": 0.0,
                                         "persName.trait[type:ethnicity].label": 0.0,
                                         "placeName.persName": 0.0,
                                         "time": 0.0,
                                         "": 0.0})
        # These kinds of bookish elements are repeated throughout and should be fairly quick to eliminate.
        # 'cell', 'item', 'text', 'resp', 'seg', 'edition', 'fileDesc', 'placename', 'table', 'PlaceName',
        # 'row', 'TEI', 'lb', 'author', 'placeNAme', 'label', 'note', 'list', 'personName', 'pubPlace', 'body',
        # 'placeName', 'head', 'bibl', 'lg', 'notesStmt', 'trait', 'sourceDesc', 'publicationStmt', 'pb', 'hi',
        # 'teiHeader', 'persName', 'editionStmt', 'date', 'desc', 'publisher', 'c', 'palceName', 'title', 'respStmt',
        # 'l', 'persNam', 'q', 'p', 'idno', 'person', 'persname', 'w', 'titleStmt', 'div'
        self.merge_with_next_tags = ["trait[type:ethnicity]", "trait[type:race]", "trait[type:religion]"]
        self.forbidden_tags = ["hi", "w", "label", "trait[type:ethnicity]", "trait[type:race]", "trait[type:religion]",
                               "trait[type:ethnicity].desc", "date", "desc", "emph", "p", "figure",
                               "table", "row", "cell", "lg", "l", "seg", "title", "q", "list", "item"]
        for t in self.tags_of_interest.keys():
            if t in self.forbidden_tags:
                self.forbidden_tags.remove(t)

    def print_ner_stats(self):
        all_counts = sum(self.tags_of_interest.values()) + 1e-32
        res = "\nFileName: {}\n".format(self.content_file_name)
        for tag in self.tags_of_interest.keys():
            if self.tags_of_interest[tag]:
                res += "\t{}: {}/{} ({:.4f}%)\n".format(tag if tag != "" else "other", int(self.tags_of_interest[tag]),
                                                        int(all_counts), self.tags_of_interest[tag]/all_counts)
        print(res.strip())

    # Call when an element starts
    def startElement(self, tag, attributes):
        # print("Start Element: \"{}\" with attribute: {}".format(tag, attributes.items()))
        # <div type="preface">
        if tag == "body":
            self.inside_body = True
        elif tag == "p":
            self.inside_p = True
        elif tag == "div" and "type" in attributes.keys() and attributes["type"] == "preface":
            self.inside_preface = True
        # atts = [(k, v) for k, v in attributes.items() if k not in ["xmlns", "rend"]]
        if len(attributes) and tag == "trait" and "type" in attributes.keys():
            # self.traverse_stack.append(tag+"["+",".join([k+":"+v for k, v in atts])+"]")
            self.traverse_stack.append(tag + "[type:"+attributes["type"]+"]")
        elif len(attributes) and tag == "div" and "type" in attributes.keys() and attributes["type"] == "preface":
            # self.traverse_stack.append(tag+"["+",".join([k+":"+v for k, v in atts])+"]")
            self.traverse_stack.append(tag + "[type:"+attributes["type"]+"]")
        else:
            self.traverse_stack.append(tag)

    # Call when an elements ends
    def endElement(self, tag):
        # print("End Element : {}".format(tag))
        # if tag == "p" and self.inside_body:
        #    exit()
        if tag == "body":
            self.inside_body = False
        elif tag == "p":
            self.inside_p = False
        elif tag == "div" and self.traverse_stack[-2] == "front" and self.traverse_stack[-1] == "div[type:preface]":
            self.inside_preface = False
        if tag == "pb":
            self.page_break_has_just_happened = True
        else:
            self.page_break_has_just_happened = False

        popped = self.traverse_stack.pop()
        assert popped.split("[")[0] == tag

    def store_tag_content(self, tag_name, content):
        assert tag_name in self.tags_of_interest.keys(), "found the tag to be %s" % ".".join(self.traverse_stack)
        if tag_name == "date.persName":
            print("Potentially invalid tag detected: date.persName in \"{}\" with the text \"{}\"\n\n".format(
                ".".join(self.traverse_stack), content))
        elif tag_name == "roleName.persName":
            print("Potentially invalid tag detected: roleName.persName in \"{}\" with the text \"{}\"\n\n".format(
                ".".join(self.traverse_stack), content))
        for word in content.strip().split():
            if self.page_break_has_just_happened:
                self.page_break_has_just_happened = False
                if len(self.text_buffer) and self.text_buffer[-1].endswith("-"):
                    # merge the "-ing" in the next page into the stem in the previous page.
                    print("Warning: you might need to take care of merging tokens in page breaks!")
            self.text_buffer.append(word)
            if tag_name == "persName" or tag_name == "placeName.persName":
                self.ner_buffer.append("I-PERS" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("PERS")
                                       else "B-PERS")
            elif tag_name == "date":
                self.ner_buffer.append("I-DATE" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("DATE")
                                       else "B-DATE")
            elif tag_name == "time":
                self.ner_buffer.append("I-TIME" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("TIME")
                                       else "B-TIME")
            elif tag_name == "placeName" or tag_name == "roleName.placeName" \
                    or tag_name == "trait[type:ethnicity].label.placeName":
                self.ner_buffer.append("I-PLCE" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("PLCE")
                                       else "B-PLCE")
            elif tag_name == "roleName" or tag_name == "trait[type:ethnicity].label.roleName" \
                    or tag_name == "persName.roleName" or tag_name == "trait[type:religion].label.roleName":
                self.ner_buffer.append("I-ROLE" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("ROLE")
                                       else "B-ROLE")
            elif tag_name == "orgName" or tag_name == "orgName.orgName" or tag_name == "roleName.orgName":
                self.ner_buffer.append("I-ORGZ" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("ORGZ")
                                       else "B-ORGZ")
            elif tag_name == "trait[type:ethnicity].label" or tag_name == "roleName.trait[type:religion].label" \
                    or tag_name == "persName.trait[type:ethnicity].label":
                self.ner_buffer.append("I-ETHY" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("ETHY")
                                       else "B-ETHY")
            elif tag_name == "trait[type:race].label":
                self.ner_buffer.append("I-RACE" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("RACE")
                                       else "B-RACE")
            elif tag_name == "trait[type:religion].label":
                self.ner_buffer.append("I-RELG" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("RELG")
                                       else "B-RELG")
            elif tag_name == "date.persName" or tag_name == "roleName.persName":
                self.ner_buffer.append("I-PERS" if len(self.ner_buffer) and self.ner_buffer[-1].endswith("PERS")
                                       else "B-PERS")
            else:
                self.ner_buffer.append("O")
            self.tags_of_interest[tag_name] += 1

            word_bare = ''.join(x.lower() for x in word if x.isalpha())
            word_is_roman_numeral = not set(word_bare.upper()).difference('MDCLXVI()')
            word_is_numeral = word_bare.isnumeric()
            """
            "Esq.", "St.", "st.", "Mr.", "mr.", "mrs.", "i.e.", "a.d.", "A.D.", "etc.", "Etc.", "vol.", "Vol.","Notit.", 
            "Imper.", "Dr.", "dr.", "Messrs.", "messrs.", "Rav.", "Chor.", "Anton.", "Not.", "Imp.", "Rev.", "Mrs."
            """
            if word.endswith(".") and not word_is_roman_numeral and not word_is_numeral and len(word_bare) != 1 and \
                    self.ner_buffer[-1] == "O" and \
                    word_bare not in ["esq", "st", "mr", "ie", "ad", "etc", "vol", "notit", "imper", "dr", "messrs",
                                      "rav", "chor", "anton", "not", "imp", "rev", "mrs", "hist", "cr"]:
                self.text_result_file.write(" ".join(self.text_buffer))
                self.text_result_file.write("\n")
                self.text_result_file.flush()
                del self.text_buffer[:]

                self.ner_result_file.write(" ".join(self.ner_buffer))
                self.ner_result_file.write("\n")
                self.ner_result_file.flush()
                del self.ner_buffer[:]

    def content_is_valid_text(self, content):
        """
        the content of the tags holding this criteria are invalid 1) all capital case 2) no tag happens in it
        """
        tmp = ''.join(x for x in content if x.isalpha())
        if len(tmp) and tmp == tmp.upper() and self.traverse_stack[-1] not in self.tags_of_interest.keys():
            return False
        elif self.page_break_has_just_happened and content.isnumeric():
            return False
        elif self.page_break_has_just_happened and not set(content.upper()).difference('MDCLXVI()'):
            # Roman Numerals
            return False
        else:
            return True

    # Call when a text is read
    def characters(self, content):
        # tags are located in the "text.body.div.p"; tags could also appear in <div type="preface">
        #  Rule if there is a word ending in "-" and a page break happens then merge the next word with this one.
        if (self.inside_body or self.inside_preface) and self.inside_p and len(content.strip()) \
                and self.traverse_stack[-1] != "seg" and self.content_is_valid_text(content):
            tmp_pt_list = [x for x in self.traverse_stack[4:]]
            pt_list = []
            for i in range(len(tmp_pt_list)):
                if tmp_pt_list[i] in self.merge_with_next_tags and i < len(tmp_pt_list) - 1:
                    pt_list.append(tmp_pt_list[i] + "." + tmp_pt_list[i+1])
                else:
                    pt_list.append(tmp_pt_list[i])

            for forbidden_tag in self.forbidden_tags:
                while forbidden_tag in pt_list:
                    pt_list.remove(forbidden_tag)
            actual_tag = ".".join([x for x in pt_list])
            self.store_tag_content(actual_tag, content)


if __name__ == "__main__":
    # create an XMLReader
    xml_files = ["books/2757 Tagged Fergus_Naomi_AST3_ML.xml", "books/1112 Tagged_ML.xml",
                 "books/Jameson vol.1-AST.xml", "books/27810-RB-SW_ML.xml"]
    for parsing_xml_file_name in xml_files:
        parser = xml.sax.make_parser()
        # turn off namepsaces
        parser.setFeature(xml.sax.handler.feature_namespaces, 0)
        # override the default ContextHandler
        Handler = TEISAXHandler(parsing_xml_file_name)
        parser.setContentHandler(Handler)
        parser.parse(parsing_xml_file_name)
        Handler.print_ner_stats()
