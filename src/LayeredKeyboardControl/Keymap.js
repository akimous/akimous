const editorCommandKeymap = {
    'u': 'goLineUp',
    'e': 'goLineDown',
    'n': 'goGroupLeft',
    'i': 'goGroupRight',
    
    'h': 'goLineLeftSmart',
    'o': 'goLineRight',
    'l': 'goLineUp5X',
    'y': 'goLineDown5X',
    'j': 'goDocStart',
    ';': 'goDocEnd',
    
    'f': 'scrollUp',
    's': 'scrollDown',
    'c': 'focusAtCenter',
    
    'r': 'moveLineDown',
    'w': 'moveLineUp',
    
    'p': 'selectLine',
    'd': 'selectScope',
    't': 'selectSmart',
    
    'backspace': 'delGroupBefore',
    'delete': 'delGroupAfter',
    
}

const completionCommandKeymap = {
    'u': 'up',
    'e': 'down',
    'l': 'up5X',
    'y': 'down5X',
}

export default {
    editorCommandKeymap,
    completionCommandKeymap
}