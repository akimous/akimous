# Jedi breaks frequently after 0.10.2.
# Here is some regression tests to make sure Jedi is not going to break this app

import jedi


def test_keyword_completion():
    completions = jedi.Script('def a():\n pa').complete()
    assert len(completions) == 1
    assert completions[0].name == 'pass'


def test_call_signatures():
    code = 'from scipy.fftpack import fft\nfft()'
    call_signatures = jedi.Script(code).get_signatures(2, 4)
    assert len(call_signatures) == 1
    assert call_signatures[0].name == 'fft'
    assert len(call_signatures[0].docstring())
