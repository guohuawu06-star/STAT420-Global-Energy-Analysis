import argparse

from src.analyze_data import analyze
from src.clean_data import clean
from src.download_data import download
from src.load_database import load
from src.make_figures import make_figures
from src.profile_data import profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", choices=("postgres", "sqlite"), required=True)
    args = parser.parse_args()
    download()
    clean(profile())
    print(load(args.db))
    print(analyze())
    make_figures()


if __name__ == "__main__":
    main()
