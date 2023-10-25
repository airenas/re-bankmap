generate: proto-v2.png proto-v1.png proto-v3.png

%.png: %.puml 
	cat $< | docker run --rm -i think/plantuml -tpng > $@_
	mv $@_ $@
