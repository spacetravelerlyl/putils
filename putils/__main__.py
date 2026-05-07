"""Entry point for python -m putils."""

# Changed from relative import to absolute import for PyInstaller compatibility
from putils.app import main


if __name__ == "__main__":
    main()
