install:
	pip install pygame Pillow --user --quiet
	pip install flake8 mypy --user --quiet

run:
	python3 a_maze_ing.py config.txt

debug:
	python3 -m pdb a_maze_ing.py config.txt

lint:
	flake8 . && mypy . --warn-return-any --warn-unused-ignores \
	  --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 . && mypy . --strict

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null; \
	true
