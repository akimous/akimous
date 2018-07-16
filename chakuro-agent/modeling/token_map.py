from collections import defaultdict
_EMPTY = tuple()


def _get_0():
    return 0


class TokenMap:
    def __init__(self):
        self.line_to_id = defaultdict(_get_0)
        self.line_to_tokens = defaultdict(set)
        self.token_to_lines = defaultdict(set)

    def remove_line(self, line):
        if self.line_to_id.pop(line, None) is None:
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
        old_id = self.line_to_id[line]
        new_id = id(line_content)
        if old_id != new_id:
            return True
        return False

    # def add_line(self, line, line_content, tokens):
    #     self.line_to_id[line] = id(line_content)
    #     line_to_tokens = self.line_to_tokens
    #     token_to_lines = self.token_to_lines
    #     for token in tokens:
    #         line_to_tokens[line].add(token)
    #         token_to_lines[token].add(line)

    def add(self, line, line_content, token):
        self.line_to_id[line] = id(line_content)
        self.line_to_tokens[line].add(token)
        self.token_to_lines[token].add(line)

    def query(self, token):
        return self.token_to_lines.get(token, None)


