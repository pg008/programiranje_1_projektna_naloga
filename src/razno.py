import sys
import unicodedata
from fuzzywuzzy import fuzz


def progressbar(it, prefix="", size=60, out=sys.stdout): # Python3.3+
    count = len(it)
    def show(j):
        x = int(size*j/count)
        print("{}[{}{}] {}/{}".format(prefix, "#"*x, "."*(size-x), j, count), 
                end='\r', file=out, flush=True)
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    print("\n", flush=True, file=out)

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def podobnost(a, b) -> int:
    if a is None or b is None: return 0
    a, b = strip_accents(a), strip_accents(b)
    a = a.replace("-", " ").upper()
    b = b.replace("-", " ").upper()

    return fuzz.token_sort_ratio(a, b)