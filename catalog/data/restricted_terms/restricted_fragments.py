# -*- coding: utf-8 -*-
from __future__ import unicode_literals
'''
List of reserved usernames (pre-defined list of special banned and reserved keywords in names,
such as "root", "www", "admin"). Useful when creating public systems, where users can choose 
a login name or a sub-domain name.
__References:__
1. http://www.bannedwordlist.com/
2. http://blog.postbit.com/reserved-username-list.html
'''

_d = ("nigger ")

wordlist = set(_d.split(" "))

def is_restricted_fragment(username):
    for word in wordlist:
        if word in username and word != "":
            return True
    return False

__all__ = ["wordlist", "is_restricted_fragment"]