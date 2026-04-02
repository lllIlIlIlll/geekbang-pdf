/**
 * Scroll content container to load all dynamic content.
 * Scrolls through the content to trigger lazy loading.
 */
function scrollContentContainer() {
    let scrollContainer = null;
    let maxHeight = 0;

    document.querySelectorAll('div').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
            style.overflow === 'auto' || style.overflow === 'scroll') {
            const scrollHeight = el.scrollHeight;
            const rect = el.getBoundingClientRect();
            if (scrollHeight > maxHeight && rect.height > 500 &&
                !el.className.includes('sidebar') &&
                !el.className.includes('catalog') &&
                !el.className.includes('menu') &&
                !el.className.includes('nav') &&
                !el.className.includes('list')) {
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
