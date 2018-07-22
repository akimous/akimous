from collections import defaultdict
_EMPTY = tuple()


class DirtyMap:
    def __init__(self):
        self.line_to_content = defaultdict(str)

    def is_dirty(self, line, line_content):
        if self.line_to_content[line] is not line_content:
            return True
        return False

    def get_dirty_lines(self, doc):
        result = []
        for line_number, line_content in enumerate(doc):
            if self.is_dirty(line_number, line_content):
                result.append(line_number)
        return result

    def set_clear(self, line, line_content):
        self.line_to_content[line] = line_content


class TokenMap:
    def __init__(self):
        self.line_to_tokens = defaultdict(set)
        self.token_to_lines = defaultdict(set)

    def remove_line(self, line):
        tokens = self.line_to_tokens.pop(line, _EMPTY)
        line_to_remove = {line}
        for token in tokens:
            lines = self.token_to_lines.get(token, _EMPTY)
            if len(lines) == 1:
                del self.token_to_lines[token]
            else:
                lines -= line_to_remove

    def add(self, line, token):
        self.line_to_tokens[line].add(token)
        self.token_to_lines[token].add(line)

    def query(self, token):
        return self.token_to_lines.get(token, None)


