#!/usr/bin/env python
try:
    import postmarkup
except:
    print "Requires Postmarkup (http://code.google.com/p/postmarkup/)"
    raise

post = postmarkup.create()
feed = postmarkup.create()
