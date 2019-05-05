const editorCommandKeyMap = {
    'KeyI': 'goLineUp',
    'KeyK': 'goLineDown',
    'KeyJ': 'goGroupLeft',
    'KeyL': 'goGroupRight',
    
    'KeyH': 'goLineLeftSmart',
    'Semicolon': 'goLineRight',
    'KeyU': 'goLineUp5X',
    'KeyO': 'goLineDown5X',
    'KeyY': 'goDocStart',
    'KeyP': 'goDocEnd',
    
    'BracketLeft': 'goToPreviousBracket',
    'BracketRight': 'goToNextBracket',
    
    'KeyE': 'scrollUp',
    'KeyD': 'scrollDown',
    'KeyC': 'focusAtCenter',
    
    'KeyW': 'swapLineUp',
    'KeyS': 'swapLineDown',
    
    'KeyR': 'selectLine',
    'KeyT': 'selectScope',
    'KeyF': 'selectSmart',
    'KeyG': 'selectBetweenBrackets',
    
    'Backspace': 'delGroupBefore',
    'Delete': 'delGroupAfter',
    
    'Digit0': 'unfoldAll',
    'Minus': 'fold',
    'Equal': 'unfold',
}

const genericCommandKeyMap = {
    'KeyI': 'up',
    'KeyK': 'down',
    'KeyU': 'up5X',
    'KeyO': 'down5X',
    'KeyJ': 'left',
    'KeyL': 'right',
    'KeyY': 'top',
    'KeyP': 'bottom',
    'KeyH': 'home',
    'Semicolon': 'end',
    
    'KeyE': 'scrollUp',
    'KeyD': 'scrollDown',
    
    'Space': 'commit',
    
    'KeyN': 'togglePanelLeft',
    'KeyM': 'panelLeft',
    'Comma': 'panelMiddle',
    'Period': 'panelRight',
    'Slash': 'togglePanelRight',
    
    'Digit1': '1',
    'Digit2': '2',
    'Digit3': '3',
    'Digit4': '4',
    'Digit5': '5',
    'Digit6': '6',
    'Digit7': '7',
    'Digit8': '8',
}

export default {
    editorCommandKeyMap,
    genericCommandKeyMap
}