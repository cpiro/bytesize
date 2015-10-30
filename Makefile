SPHINX = html doctest

.PHONY: all test sphinx $(SPHINX)

all:
	@echo nah bruh

test:
	nosetests --with-coverage --cover-package=bytesize

sphinx: $(SPHINX)

$(SPHINX):
	$(MAKE) -C docs $@
