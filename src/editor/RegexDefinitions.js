const OPERATOR = /((\/\/=|>>=|<<=|\*\*=)|([+\-*/%&|^@!<>=]=)|(<>|<<|>>|\/\/|\*\*|->)|[+\-*/%&|^~<>!@=])$/
const COMPOUND_OPERATOR = /((\/\/=|>>=|<<=|\*\*=)|([+\-*/%&|^@!<>=]=)|(<>|<<|>>|\/\/|\*\*|->))$/
const OPERATOR_CHARACTOR = /[=+\-*/|&^~%@><!]$/
const IDENTIFIER = /^[^\d\W]\w*$/

export {
    OPERATOR, COMPOUND_OPERATOR, OPERATOR_CHARACTOR, IDENTIFIER
}