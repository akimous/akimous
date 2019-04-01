describe('Open', () => {
    beforeAll(async () => {
        await page.goto('http://localhost:3179/')
    })

    it('Menu bar displayed', async () => {
        await expect(page).toMatch('File')
    })
})
