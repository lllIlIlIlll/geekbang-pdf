/**
 * Remove floating layers from the page.
 * Removes fixed/sticky positioned elements like modals, popups, overlays.
 */
function removeFloatingLayers() {
    const toRemove = [];
    document.querySelectorAll('*').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.position === 'fixed' || style.position === 'sticky') {
            const text = el.innerText || '';
            const classes = el.className || '';
            if ((text.includes('登录') && text.includes('注册')) ||
                text.includes('推荐试读') ||
                text.includes('仅针对订阅') ||
                classes.includes('modal') ||
                classes.includes('popup') ||
                classes.includes('overlay')) {
                toRemove.push(el);
            }
        }
    });
    toRemove.forEach(el => el.remove());
    return { removedCount: toRemove.length };
}
