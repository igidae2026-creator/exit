import os


def check():
    if not os.path.exists("artifact_store"):
        raise Exception("artifact store missing")
