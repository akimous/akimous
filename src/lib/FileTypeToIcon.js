const fileTypeToIcon = {
    'default': 'fa fa-file-o l-ui-text',
    'loading': 'fa fa-hourglass-half l-ui-text',
    'folder': 'fa fa-folder l-ui-text',
    'folder-open': 'fa fa-folder-open l-ui-text',

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
    'class': 'devicon-java-plain l-green',
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

    '7z': 'fa fa-archive l-olive',
    'aac': 'fa fa-music l-yellow',
    'bat': 'fa fa-terminal l-red',
    'bin': 'fa fa-file l-red',
    'cmd': 'fa fa-terminal l-green',
    'config': 'fa fa-cog l-green',
    'csv': 'fa fa-table l-green',
    'db': 'fa fa-database l-blue',
    'db2': 'fa fa-database l-red',
    'db3': 'fa fa-database l-green',
    'doc': 'fa fa-file-word-o l-blue',
    'docx': 'fa fa-file-word-o l-blue',
    'exe': 'fa fa-windows l-orange',
    'flac': 'fa fa-music l-green',
    'gif': 'fa fa-file-image-o l-olive',
    'gz': 'fa fa-file-archive-o l-olive',
    'ico': 'fa fa-file-image-o l-white',
    'ini': 'fa fa-cog l-white',
    'jpg': 'fa fa-camera l-slate',
    'jpeg': 'fa fa-camera l-slate',
    'json': 'fa fa-cog l-orange',
    'log': 'fa fa-file-text-o l-white',
    'md': 'fa fa-arrow-down l-white',
    'mid': 'fa fa-music l-blue',
    'midi': 'fa fa-music l-blue',
    'mp3': 'fa fa-music l-red',
    'mp4': 'fa fa-film l-red',
    'o': 'fa fa-object-ungroup l-white',
    'ogg': 'fa fa-file-audio-o l-white',
    'png': 'fa fa-picture-o l-red',
    'pkg': 'fa fa-cube l-purple',
    'ppt': 'fa fa-file-powerpoint-o l-red',
    'pptx': 'fa fa-file-powerpoint-o l-red',
    'rar': 'fa fa-archive l-purple',
    'rs': 'fa fa-cog l-gray',
    'rst': 'fa fa-align-left l-gray',
    'svg': 'fa fa-file-image-o l-green',
    'sh': 'fa fa-terminal l-white',
    'so': 'fa fa-share-square l-gray',
    'tar': 'fa fa-file-archive-o l-gray',
    'ttf': 'fa fa-font l-orange',
    'txt': 'fa fa-file-text l-gray',
    'wav': 'fa fa-volume-up l-blue',
    'woff': 'fa fa-font l-blue',
    'woff2': 'fa fa-font l-red',
    'xls': 'fa fa-file-excel-o l-green',
    'xlsx': 'fa fa-file-excel-o l-green',
    'xml': 'fa fa-code l-orange',
    'xz': 'fa fa-archive l-red',
    'yaml': 'fa fa-percent l-red',
    'zip': 'fa fa-archive l-orange',
}

const defaultIcon = fileTypeToIcon['default']
const folderIcon = fileTypeToIcon['folder']
const folderOpenIcon = fileTypeToIcon['folder-open']

export {
    fileTypeToIcon,
    defaultIcon,
    folderIcon,
    folderOpenIcon
}