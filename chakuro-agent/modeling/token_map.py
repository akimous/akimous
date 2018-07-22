from collections import defaultdict
_EMPTY = tuple()


class TokenMap:
    def __init__(self):
        self.line_to_content = defaultdict(str)
        self.line_to_tokens = defaultdict(set)
        self.token_to_lines = defaultdict(set)

    def remove_line(self, line):
        if self.line_to_content.pop(line, None) is None:
            return
        tokens = self.line_to_tokens.pop(line, _EMPTY)
        line_to_remove = {line}
        for token in tokens:
            lines = self.token_to_lines.get(token, _EMPTY)
            if len(lines) == 1:
                del self.token_to_lines[token]
            else:
                lines -= line_to_remove

    def dirty(self, line, line_content):
        if self.line_to_content[line] is not line_content:
            return True
        return False

    def get_dirty_lines(self, doc):
        result = []
        for line_number, line_content in enumerate(doc):
            if self.dirty(line_number, line_content):
                result.append(line_number)
        return result

    def add(self, line, line_content, token):
        self.line_to_content[line] = line_content
        self.line_to_tokens[line].add(token)
        self.token_to_lines[token].add(line)

    def add_line_with_no_tokens(self, line, line_content):
        self.line_to_content[line] = line_content

    def query(self, token):
        return self.token_to_lines.get(token, None)


