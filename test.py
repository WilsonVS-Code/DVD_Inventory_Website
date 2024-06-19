import imdb

def check_imdbpy():
    try:
        print(f"IMDbPY is installed correctly! Version: {imdb.__version__}")
    except AttributeError:
        print("IMDbPY is installed but version could not be determined.")

if __name__ == "__main__":
    check_imdbpy()
