import keyboardJS from 'keyboardjs'
import g from '../lib/Globals'

function bindHotkeys() {
    function hotkey(key, handler) {
        keyboardJS.bind(key, e => {
            e.preventDefault()
            return handler(e)
        })
    }

    hotkey('mod + s', g.saveFile)

    hotkey('mod + shift + s', () => {
        g.saveAll()
    })

    hotkey('mod + f', () => {
        g.setFocus([g.panelRight, g.find])
        g.find.$set({ 
            active: true,
            replaceMode: false,
            findInDirectory: null,
            matches: [],
            selectedIndex: -1,
        })
        requestAnimationFrame(() => {
            g.find.findTextInput.focus()
        })
    })

    const replaceMode = () => {
        g.setFocus([g.panelRight, g.find])
        g.find.$set({ 
            active: true,
            replaceMode: true,
            findInDirectory: null,
        })
        requestAnimationFrame(() => {
            g.find.findTextInput.focus()
        })
    }
    hotkey('mod + alt + f', replaceMode)
    hotkey('mod + h', replaceMode)

    hotkey('mod + g', () => {
        g.find.find(1)
        g.find.findNextButton.flash()
    })

    hotkey('mod + shift + g', () => {
        g.find.find(-1)
        g.find.findPreviousButton.flash()
    })

    hotkey('mod + `', () => {
        if (!g.activeEditor) return
        const { filePath } = g.activeEditor
        filePath && g.panelMiddle.closeFile(filePath)
    })

    const canBeRenamed = token => {
        return token.string.length > 0 && token.type &&
            (token.type.includes('variable') || token.type.includes('def'))
    }
    hotkey('f8', () => {
        const editor = g.activeEditor
        if (!editor) return
        const cm = editor.cm
        const cursor = cm.getCursor('to')
        let token = cm.getTokenAt(cursor)
        if (!canBeRenamed(token)) {
            cursor.ch += 1
            token = cm.getTokenAt(cursor)
        }
        if (!canBeRenamed(token)) {
            g.notificationBar.show('warning', 'Please select a variable.')
            return
        }
        editor.session.send('FindUsages', {
            line: cursor.line,
            ch: cursor.ch,
            token: token.string
        })
    })
    hotkey('f1', () => {
        g.panelLeft.tabBar.switchToTab(1)
    })
    hotkey('f2', () => {
        g.panelLeft.tabBar.switchToTab(2)
    })
    for (let i = 1; i < 6; i++)
        hotkey('f' + (i + 2), () => {
            g.panelRight.tabBar.switchToTab(i)
        })
    
    
    hotkey('mod + r', () => {
        g.console.runDefault()
    })
}
export default {
    bindHotkeys
}
