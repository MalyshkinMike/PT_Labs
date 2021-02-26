# -*- coding: utf-8 -*-
import json
END_CHARACTER = "\0"
TARGET_ENCODING = "utf-8"
class Message(object):
    def __init__(self, **kwargs):
        self.message = None
        self.quit = False
        self.end_turn = False
        self.username = None
        self.__dict__.update(kwargs)


    def marshal(self):
        return (json.dumps(self.__dict__) + END_CHARACTER).encode(TARGET_ENCODING)
