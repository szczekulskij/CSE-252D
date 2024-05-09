import os 
def delete_based_on_filepaths(filenames):
    for filepath in filenames:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            print(f"File not found: {filepath}")


if __name__ == "__main__":
    # parse args from terminal
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filenames", type=str, nargs="+")
    args = parser.parse_args()
    delete_based_on_filepaths(args.filepaths)