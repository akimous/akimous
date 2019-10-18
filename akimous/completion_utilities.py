def is_parameter_of_def(doc, line, ch):
    open_brackets = {'(': ')', '[': ']', '{': '}'}
    close_brackets = {')', ']', '}'}
    def_line = -1
    for l in range(line, max(-1, line - 20), -1):
        line_content = doc[l]
        if line_content.strip().startswith('def '):
            def_line = l
            break
    if def_line == -1:
        return False

    stack = []
    for l in range(def_line, line + 1):
        line_content = doc[l]
        for c, char in enumerate(line_content):
            if l == line and c == ch:
                if len(stack) == 1 and stack[0] == '(':
                    return True
                return False
            if l != line and '):' in line_content:
                return False
            if char in open_brackets:
                stack.append(char)
            if char in close_brackets and open_brackets[stack[-1]] == char:
                stack.pop()
    return False
