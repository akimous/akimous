from collections import namedtuple

Rule = namedtuple('Rule', ('name', 'function', 'priority'))


class RuleBasedPredictor:
    rules = []

    def __init__(self):
        RuleBasedPredictor.rules.sort(key=lambda x: -x.priority)

    def predict(self, **kwargs):
        results = [rule.function(**kwargs) for rule in RuleBasedPredictor.rules]
        return results

    @staticmethod
    def register_rule(name, priority=0):
        def inner(f):
            RuleBasedPredictor.rules.append(Rule(name, f, priority))
            return f
        return inner


@RuleBasedPredictor.register_rule('same_statement_as_above')
def f(top_completion, doc, line, ch, **_):
    last_line_tail = doc[line - 1][ch:]
    if last_line_tail.startswith(top_completion.complete):
        offset = top_completion.name.find(top_completion.complete)
        return top_completion.name[:offset] + last_line_tail
    return None
