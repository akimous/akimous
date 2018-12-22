from jedi import Script

doc = 'def a():\n    pa\n'


class DummyString(str):
    def __init__(self, doc):
        super(str)
        self._doc = doc

    def splitlines(self, keepends):
        return list(self._doc)

    def endswith(self, suffix):
        return False

    def __eq__(self, other):
        return False

# s = Script(doc)
# print(s.completions())


d = DummyString(doc.splitlines(True))
s = Script(d, 2, 6)
print(d._doc)
print(s.completions())

d._doc.insert(2, '\n')
d = DummyString(d._doc)
print(d._doc)
s = Script(d, 2, 6)
print(s.completions())