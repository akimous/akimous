def detect_doc_type(docstring):
    if '-----' in docstring:
        return 'NumPyDoc'
    if 'Args:' in docstring or 'Returns:' in docstring:
        return 'GoogleDoc'
    if ':param ' in docstring or ':returns:' in docstring:
        return 'rst'
    return 'text'
