#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS 
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, 
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import sys
import os
import signal
import json
from threading import Thread
from PIL import Image



def load(location, auto_dump, sig=True):
    '''Return a HashTable object. location is the path to the json file.'''
    return HashTable(location, auto_dump, sig)


class HashTable(object):

    key_string_error = TypeError('Key/name must be a string!')

    def __init__(self, location, auto_dump, sig):
        '''Creates a hashtable object and loads the data from the location path.
        If the file does not exist it will be created on the first update.
        '''
        self.load(location, auto_dump)
        self.dthread = None
        if sig:
            self.set_sigterm_handler()

    def __getitem__(self, item):
        '''Syntax sugar for get()'''
        return self.get(item)

    def __setitem__(self, key, value):
        '''Sytax sugar for set()'''
        return self.set(key, value)

    def __delitem__(self, key):
        '''Sytax sugar for rem()'''
        return self.rem(key)

    def __average_hash__(self, image_path, hash_size=8):
        """ Compute the average hash of the given image. """
        # print(image_path)
        with open(image_path, 'rb') as f:
            # Open the image, resize it and convert it to black & white.
            image = Image.open(f).resize((hash_size, hash_size), Image.ANTIALIAS).convert('L')
            pixels = list(image.getdata())

        avg = sum(pixels) / len(pixels)

        # Compute the hash based on each pixels value compared to the average.
        bits = "".join(map(lambda pixel: '1' if pixel > avg else '0', pixels))
        hashformat = "0{hashlength}x".format(hashlength=hash_size ** 2 // 4)
        return int(bits, 2).__format__(hashformat)    

    def set_sigterm_handler(self):
        '''Assigns sigterm_handler for graceful shutdown during dump()'''
        def sigterm_handler():
            if self.dthread is not None:
                self.dthread.join()
            sys.exit(0)
        signal.signal(signal.SIGTERM, sigterm_handler)

    def load(self, location, auto_dump):
        '''Loads, reloads or changes the path to the ht file'''
        location = os.path.expanduser(location)
        self.loco = location
        self.auto_dump = auto_dump
        if os.path.exists(location):
            self._loadht()
        else:
            self.ht = {}
        return True

    def dump(self):
        '''Force dump memory ht to file'''
        json.dump(self.ht, open(self.loco, 'wt'))
        self.dthread = Thread(
            target=json.dump,
            args=(self.ht, open(self.loco, 'wt')))
        self.dthread.start()
        self.dthread.join()
        return True

    def _loadht(self):
        '''Load or reload the json info from the file'''
        try: 
            self.ht = json.load(open(self.loco, 'rt'))
        except ValueError:
            if os.stat(self.loco).st_size == 0:  # Error raised because file is empty
                self.ht = {}
            else:
                raise  # File is not empty, avoid overwriting it

    def _autodumpht(self):
        '''Write/save the json dump into the file if auto_dump is enabled'''
        if self.auto_dump:
            self.dump()

    def set(self, key, value):
        '''Set the str value of a key'''
        if isinstance(key, str):
            self.ht[key] = value
            self._autodumpht()
            return True
        else:
            raise self.key_string_error

    def get(self, key):
        '''Get the value of a key'''
        try:
            return self.ht[key]
        except KeyError:
            return False

    def rem(self, key):
        '''Delete a key'''
        if not key in self.ht: # return False instead of an exception
            return False
        del self.ht[key]
        self._autodumpht()
        return True

    def lcreate(self, name):
        '''Create a list, name must be str'''
        if isinstance(name, str):
            self.ht[name] = []
            self._autodumpht()
            return True
        else:
            raise self.key_string_error

    def ladd(self, name, value):
        '''Add a value to a list'''
        self.ht[name].append(value)
        self._autodumpht()
        return True

    def lextend(self, name, seq):
        '''Extend a list with a sequence'''
        self.ht[name].extend(seq)
        self._autodumpht()
        return True

    def lgetall(self, name):
        '''Return all values in a list'''
        return self.ht[name]

    def lget(self, name, pos):
        '''Return one value in a list'''
        return self.ht[name][pos]

    def lrange(self, name, start=None, end=None):
        '''Return range of values in a list '''
        return self.ht[name][start:end]

    def lremlist(self, name):
        '''Remove a list and all of its values'''
        number = len(self.ht[name])
        del self.ht[name]
        self._autodumpht()
        return number

    def lremvalue(self, name, value):
        '''Remove a value from a certain list'''
        self.ht[name].remove(value)
        self._autodumpht()
        return True

    def lpop(self, name, pos):
        '''Remove one value in a list'''
        value = self.ht[name][pos]
        del self.ht[name][pos]
        self._autodumpht()
        return value

    def llen(self, name):
        '''Returns the length of the list'''
        return len(self.ht[name])

    def lappend(self, name, pos, more):
        '''Add more to a value in a list'''
        tmp = self.ht[name][pos]
        self.ht[name][pos] = tmp + more
        self._autodumpht()
        return True

    def lexists(self, name, value):
        '''Determine if a value  exists in a list'''
        return value in self.ht[name]

    def dcreate(self, name):
        '''Create a dict, name must be str'''
        if isinstance(name, str):
            self.ht[name] = {}
            self._autodumpht()
            return True
        else:
            raise self.key_string_error

    def dadd(self, name, pair):
        '''Add a key-value pair to a dict, "pair" is a tuple'''
        self.ht[name][pair[0]] = pair[1]
        self._autodumpht()
        return True

    def dget(self, name, key):
        '''Return the value for a key in a dict'''
        return self.ht[name][key]

    def dgetall(self, name):
        '''Return all key-value pairs from a dict'''
        return self.ht[name]

    def drem(self, name):
        '''Remove a dict and all of its pairs'''
        del self.ht[name]
        self._autodumpht()
        return True

    def dpop(self, name, key):
        '''Remove one key-value pair in a dict'''
        value = self.ht[name][key]
        del self.ht[name][key]
        self._autodumpht()
        return value

    def dkeys(self, name):
        '''Return all the keys for a dict'''
        return self.ht[name].keys()

    def dvals(self, name):
        '''Return all the values for a dict'''
        return self.ht[name].values()

    def dexists(self, name, key):
        '''Determine if a key exists or not in a dict'''
        return key in self.ht[name]

    def dmerge(self, name1, name2):
        '''Merge two dicts together into name1'''
        first = self.ht[name1]
        second = self.ht[name2]
        first.update(second)
        self._autodumpht()
        return True

    def delht(self):
        '''Delete everything from the hashtable'''
        self.ht = {}
        self._autodumpht()
        return True



