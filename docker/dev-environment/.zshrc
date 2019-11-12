export PATH="$HOME/.poetry/bin:$PATH"
ZSH="$(antibody home)/https-COLON--SLASH--SLASH-github.com-SLASH-robbyrussell-SLASH-oh-my-zsh"
source <(antibody init)
antibody bundle < ~/.zsh_plugins.txt
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh