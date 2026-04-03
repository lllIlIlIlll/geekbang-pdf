/**
 * Scroll content container to load all dynamic content.
 * Scrolls through the content to trigger lazy loading.
 * @param {string} selectorsJson - JSON string of platform selectors
 */
function scrollContentContainer(selectorsJson) {
    const selectors = JSON.parse(selectorsJson);
    const excludeClasses = selectors.exclude_classes || [];

    let scrollContainer = null;
    let maxHeight = 0;

    document.querySelectorAll('div').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
            style.overflow === 'auto' || style.overflow === 'scroll') {
            const scrollHeight = el.scrollHeight;
            const rect = el.getBoundingClientRect();
            const className = el.className || '';
            const shouldExclude = excludeClasses.some(c => className.includes(c));
            if (scrollHeight > maxHeight && rect.height > 500 && !shouldExclude) {
                maxHeight = scrollHeight;
                scrollContainer = el;
            }
        }
    });

    if (!scrollContainer) {
        window.scrollTo(0, document.body.scrollHeight);
        return { method: 'window', scrollHeight: document.body.scrollHeight };
    }

    const finalHeight = scrollContainer.scrollHeight;
    let scrolled = 0;
    const scrollStep = window.innerHeight;

    while (scrolled < finalHeight) {
        scrollContainer.scrollTop += scrollStep;
        scrolled += scrollStep;
        if (typeof requestAnimationFrame === 'function') {
            requestAnimationFrame(() => {});
        }
    }

    scrollContainer.scrollTop = 0;

    return {
        method: 'container',
        containerClass: scrollContainer.className,
        scrollHeight: finalHeight
    };
}
