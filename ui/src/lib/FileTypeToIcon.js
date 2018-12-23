const fileTypeToIcon = {
    'default': 'far fa-file l-ui-text',
    'loading': 'fas fa-hourglass-half l-ui-text',
    'folder': 'fas fa-folder l-ui-text',
    'folder-open': 'fas fa-folder-open l-ui-text',

    'gitignore': 'devicon-git-plain colored',
    'license': 'fas fa-file-contract l-orange',
    'makefile': 'fas fa-space-shuttle l-blue',
    'lock': 'fas fa-lock l-purple',

    'ipynb': 'l-jupyter-icon',
    'py': 'l-python-icon',
    'pyc': 'devicon-python-plain l-sandybrown',
    'pyd': 'devicon-python-plain l-sandybrown',
    'pyo': 'devicon-python-plain l-sandybrown',
    'pyw': 'devicon-python-plain l-sandybrown',
    'pyx': 'devicon-python-plain l-yellow',
    'pxd': 'devicon-python-plain l-brown',

    'ai': 'devicon-illustrator-plain colored',
    'c': 'devicon-c-plain colored',
    'cc': 'devicon-c-plain l-green',
    'class': 'devicon-java-plain l-red',
    'coffee': 'devicon-coffeescript-plain l-blue',
    'cpp': 'devicon-cplusplus-plain colored',
    'cs': 'devicon-csharp-plain colored',
    'css': 'devicon-css3-plain colored',
    'dockerfile': 'devicon-docker-plain colored',
    'go': 'devicon-go-plain colored',
    'htm': 'devicon-html5-plain l-orange',
    'html': 'devicon-html5-plain colored',
    'java': 'devicon-java-plain colored',
    'js': 'devicon-javascript-plain colored',
    'less': 'devicon-less-plain-wordmark colored',
    'php': 'devicon-php-plain colored',
    'php3': 'devicon-php-plain colored',
    'php4': 'devicon-php-plain colored',
    'psd': 'devicon-photoshop-plain colored',
    'rb': 'devicon-ruby-plain colored',
    'swift': 'devicon-swift-plain colored',
    'ts': 'devicon-typescript-plain colored',

    '7z': 'fas fa-archive l-olive',
    'aac': 'fas fa-music l-yellow',
    'bat': 'fas fa-terminal l-red',
    'bin': 'fas fa-file l-red',
    'cmd': 'fas fa-terminal l-green',
    'cfg': 'fas fa-cog l-ao',
    'config': 'fas fa-cog l-green',
    'csv': 'fas fa-table l-ao',
    'db': 'fas fa-database l-blue',
    'db2': 'fas fa-database l-red',
    'db3': 'fas fa-database l-green',
    'doc': 'far fa-file-word l-blue',
    'docx': 'far fa-file-word l-blue',
    'exe': 'fab fa-windows l-orange',
    'flac': 'fas fa-music l-green',
    'gif': 'far fa-file-image l-olive',
    'gz': 'far fa-file-archive l-olive',
    'ico': 'far fa-file-image l-white',
    'ini': 'fas fa-cog l-white',
    'jpg': 'fas fa-camera l-slate',
    'jpeg': 'fas fa-camera l-slate',
    'json': 'fas fa-cog l-orange',
    'log': 'fas fa-file-alt l-white',
    'map': 'fas fa-map l-white',
    'md': 'fab fa-markdown l-ao',
    'mid': 'fas fa-music l-blue',
    'midi': 'fas fa-music l-blue',
    'mp3': 'fas fa-music l-red',
    'mp4': 'fas fa-film l-red',
    'o': 'fas fa-object-ungroup l-white',
    'ogg': 'far fa-file-audio l-white',
    'png': 'far fa-image l-red',
    'pkg': 'fas fa-cube l-purple',
    'ppt': 'far fa-file-powerpoint l-red',
    'pptx': 'far fa-file-powerpoint l-red',
    'rar': 'fas fa-archive l-purple',
    'rs': 'fas fa-cog l-gray',
    'rst': 'fas fa-align-left l-gray',
    'svg': 'far fa-file-image l-green',
    'sh': 'fas fa-terminal l-white',
    'so': 'fas fa-share-square l-gray',
    'tar': 'far fa-file-archive l-gray',
    'toml': 'fas fa-marker l-green',
    'ttf': 'fas fa-font l-orange',
    'txt': 'far fa-file-alt l-gray',
    'wav': 'fas fa-volume-up l-blue',
    'woff': 'fas fa-font l-blue',
    'woff2': 'fas fa-font l-red',
    'xls': 'far fa-file-excel l-green',
    'xlsx': 'far fa-file-excel l-green',
    'xml': 'fas fa-code l-orange',
    'xz': 'fas fa-archive l-red',
    'yaml': 'fas fa-percent l-red',
    'zip': 'fas fa-archive l-orange',
}

const defaultIcon = fileTypeToIcon['default']
const folderIcon = fileTypeToIcon['folder']
const folderOpenIcon = fileTypeToIcon['folder-open']

function getIconByFileName(fileName) {
    let icon
    try {
        const fileType = fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase()
        icon = fileTypeToIcon[fileType]
        if (!icon) {
            if (fileType.endsWith('rc'))
                return 'fas fa-sliders-h l-ao'
            if (fileType.endsWith('ignore'))
                return 'fas fa-eye-slash l-blue'
            return defaultIcon
        }
    } catch (e) {
        icon = defaultIcon
    }
    return icon
}

export {
    fileTypeToIcon,
    defaultIcon,
    folderIcon,
    folderOpenIcon,
    getIconByFileName
}
