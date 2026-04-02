/**
 * Expand content container to full height for PDF generation.
 * Removes scrolling constraints and expands to full content height.
 */
function expandContentContainer() {
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
        return { expanded: false, error: 'No container found' };
    }

    const originalScrollHeight = scrollContainer.scrollHeight;
    scrollContainer.scrollTop = originalScrollHeight;
    const loadedScrollHeight = scrollContainer.scrollHeight;
    scrollContainer.scrollTop = 0;

    scrollContainer.style.maxHeight = 'none';
    scrollContainer.style.height = (loadedScrollHeight + 500) + 'px';
    scrollContainer.style.overflow = 'visible';

    const parent = scrollContainer.parentElement;
    if (parent && (parent.className.includes('simplebar') || parent.className.includes('SimpleBar'))) {
        parent.style.maxHeight = 'none';
        parent.style.height = (loadedScrollHeight + 500) + 'px';
        parent.style.overflow = 'visible';
        const simplebarEl = parent.querySelector('.simplebar-scrollbar');
        if (simplebarEl) {
            simplebarEl.style.display = 'none';
        }
    }

    return {
        expanded: true,
        originalScrollHeight: originalScrollHeight,
        loadedScrollHeight: loadedScrollHeight,
        className: scrollContainer.className
    };
}
