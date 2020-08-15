## Machine Reading: Guide to the NER-Prep Project
The project is intended to Parse TEI-XML formatted book files, extracted information of interest out of it (e.g. Named Entities, Time tags, etc.), and transform all the books into three disjoint sets of train/test/dev, ready to be fed to any NER model working with CoNLL 2003 format.

### Project Structure
The project contains two python scripts and a directory called `books`. The directory contains all the books submitted to the project up to present moment.
If you have new books (essentially in TEI-XML format), you may put your other files in the `books` directory as well. However, the models will not pick the book up unless you explicitly mention the file name in both Python Scripts. The next sections will describe how the two scripts transform the raw XML files to CoNLL 2003 formatted datasets.

### Parser
This script uses the SAX parsing method to parse the books one after another, the intermediate output of parsing each XML file will be saved into two separate files with the same name as the XML file but ending to `.ner.txt` and `.res.txt`, the latter of which will contain the actual extracted sentences from the book while the former contains sentences of  equal size but with each word replaced with their `ner` tag.
 
You have to run the `Parser.py` script before running the next script (`Merger.py`). To add books, you have to locate the line `xml_files = [... a list of strings containig book names]` in the script (currently in line 184) and add the name of the book you want to be added (with a `books/` suffix) to the process 
at the end of this list. However, before doing so make sure you have put that xml file in the `books` directory besides the script.

You may then run the script. If the book you have added, contains unknown tags to the Parser you will very likely get an `AssertionError: found the tag to be <complete tag name>` error. You then need to look into the Parser defined tags,  and either add that tag in `self.tags_of_interest` or in `self.forbidden_tags`. You may also need to define what the model must record as the ner tag once it sees the new tag in `store_tag_content()` function. You can simply run the script using `python Parser.py` (no arguments needed!)

### Merger
This script is intended for transforming the created `.ner.txt` and `.res.txt` files in parser to single files in CoNLL 2003 format. There is also a `NON_ANNOTATED_DROP_RATIO` parameter which you can set to randomly drop some of the sentences that do not come with any annotations (it is an implementation of down sampling for our imbalanced dataset). This option has proved to be useful in this project so we recommend setting a value around at least `0.2` (20 percent). 

If you have added any new file names to the `xml_files` list in parser you will need to add the same file names (here with a `parsed/` suffix) to the `xml_files` list of `Merger.py` script (currently in line 22). To run the merger you will need to have `SpaCy` python package installed and the English language resources downloaded for it (you can simply download them using this command `python -m spacy download en`). 
 
Now you can run the merger script using `python Merger.py`. It will take a while and eventually the result files will be ready in `tagged` directory. The files will be named `result.train`, `result.valid`, and `result.test`. You may take these files and directly feed them to any NER model. 

### Results
<img src="https://raw.githubusercontent.com/Mehrdad93/Machine-Reading/master/results/DatasetStats.png">

### Contributors
> Mehrdad Mokhtari; 
> Mladen Rakovic;
> Oliver Schulte

