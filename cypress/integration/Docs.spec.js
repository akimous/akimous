describe('Doc panel', () => {
    it('gets documentation', () => {
        cy.visit('http://127.0.0.1:5000')
        cy.wait(1000)
        cy.contains('demo.py').dblclick()
        cy.contains('tests').dblclick()
        cy.contains('docs.py').click().dblclick()
    })
    it('shows documentation for RandomForest', () => {
        cy.wait(500)
        cy.get('.CodeMirror textarea').type(
            '{downarrow}'.repeat(11) + '{leftarrow}{leftarrow}', { force: true }
        )
        cy.contains('The number of trees in the forest.')
        cy.get('body').type('{ctrl}', { release: false })
        cy.get('.highlight-parameter').contains('n_estimators')
    })
//    it('adds n_estimator=10', () => {
//    })
})
