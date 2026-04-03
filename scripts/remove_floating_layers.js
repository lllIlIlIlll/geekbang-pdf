/**
 * Remove floating layers from the page.
 * Removes fixed/sticky positioned elements like modals, popups, overlays.
 * @param {string} selectorsJson - JSON string of platform selectors
 */
function removeFloatingLayers(selectorsJson) {
    const selectors = JSON.parse(selectorsJson);
    const fixedClassnames = selectors.fixed_classnames || [];
    const fixedTexts = selectors.fixed_texts || [];

    const toRemove = [];
    document.querySelectorAll('*').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.position === 'fixed' || style.position === 'sticky') {
            const text = el.innerText || '';
            const classes = el.className || '';
            let shouldRemove = fixedTexts.some(t => text.includes(t));
            if (!shouldRemove && fixedClassnames.length > 0) {
                shouldRemove = fixedClassnames.some(c => classes.includes(c));
            }
            if (shouldRemove) {
                toRemove.push(el);
            }
        }
    });
    toRemove.forEach(el => el.remove());
    return { removedCount: toRemove.length };
}
