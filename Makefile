data/external/deep/glove.840B.300d.txt:
	mkdir -p data/external/deep
	curl http://nlp.stanford.edu/data/glove.840B.300d.zip > /tmp/glove.840B.300d.zip
	unzip /tmp/glove.840B.300d.zip -d data/external/deep
	rm /tmp/glove.840B.300d.zip

output/deep/params: data/external/deep/glove.840B.300d.txt
	python3 guesser/util/format_dan.py --threshold=5
	python3 guesser/util/load_embeddings.py
	python3 guesser/dan.py

output/kenlm.binary:
	mkdir -p temp
	python3 cli.py build_mentions_lm_data data/external/wikipedia /tmp/wiki_sent
	lmplz -o 5 < /tmp/wiki_sent > output/kenlm.arpa
	build_binary output/kenlm.arpa $@
	rm /tmp/wiki_sent

output/wikifier/data/input/:
	rm -rf $@
	mkdir -p $@
	python3 qanta/wikipedia/wikification.py

output/wikifier/data/output/: output/wikifier/data/input
	rm -rf $@
	mkdir -p $@
	(cd data/external/Wikifier2013 && java -Xmx10G -jar dist/wikifier-3.0-jar-with-dependencies.jar -annotateData ~/qb/output/wikifier/data/input ~/qb/output/wikifier/data/output false configs/STAND_ALONE_NO_INFERENCE.xml)

clm/clm_wrap.cxx: clm/clm.swig
	swig -c++ -python $<

clm/clm_wrap.o: clm/clm_wrap.cxx
	gcc -O3 `python3-config --includes` -std=c++11 -fPIC -c $< -o $@

clm/clm.o: clm/clm.cpp clm/clm.h
	gcc -O3 `python3-config --includes` -std=c++11 -fPIC -c $< -o $@

clm/_clm.so: clm/clm.o clm/clm_wrap.o
	g++ -shared `python3-config --ldflags` $^ -o $@

clm: clm/_clm.so

prereqs: output/wikifier/data/output output/kenlm.binary output/deep/params clm
