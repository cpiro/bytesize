SPHINX = html doctest

.PHONY: all test nose hardcases-stability sphinx $(SPHINX)

all:
	@echo nah bruh

test: nose hardcases-stability

nose:
	nosetests --with-coverage --cover-package=bytesize

hardcases-stability:
	bash -c 'diff -U1 tests/data_for_hardcases.py <(python3 tests/test_hardcases.py generate)'

sphinx: $(SPHINX)

$(SPHINX):
	$(MAKE) -C docs $@
