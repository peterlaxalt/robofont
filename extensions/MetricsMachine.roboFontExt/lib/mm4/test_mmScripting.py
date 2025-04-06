if __name__ == "__main__":
    import importlib
    import doctest
    import mmScripting
    importlib.reload(mmScripting)
    doctest.testmod(mmScripting)