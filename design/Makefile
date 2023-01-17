generate: proto-v1.png

%.png: %.puml 
	cat $< | docker run --rm -i think/plantuml -tpng > $@_
	mv $@_ $@
