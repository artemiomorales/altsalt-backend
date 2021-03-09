import random
import string


def GenerateRandomString():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(12))