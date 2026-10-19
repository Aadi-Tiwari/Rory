"""Compatibility entrypoint for the explicit frozen-prediction evaluator.

From backend_a, run python -m models.evaluate --help.
Generate predictions first with python -m research.infer.
"""

from research.evaluate import main


if __name__ == "__main__":
    main()
