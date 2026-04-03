/**
 * Hide left sidebar and expand content area.
 * Hides the sidebar navigation and fixes right-side fixed elements.
 * @param {string} selectorsJson - JSON string of platform selectors
 */
function hideSidebarAndExpandContent(selectorsJson) {
    const selectors = JSON.parse(selectorsJson);
    const sidebarSelectors = selectors.sidebar || [];
    const articleContentSelectors = selectors.article_content || [];
    const scrollContainerSelectors = selectors.scroll_container || [];

    let hiddenCount = 0;

    // 1. Hide left sidebar
    sidebarSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
            el.style.display = 'none';
            hiddenCount++;
        });
    });

    // 2. Hide right fixed elements
    document.querySelectorAll('*').forEach(el => {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const classes = el.className || '';
        if (style.position === 'fixed' && rect.left > 1000 && rect.width < 400) {
            el.style.display = 'none';
            hiddenCount++;
        }
    });

    // 3. Find and expand main content area
    let contentEl = null;
    for (const sel of articleContentSelectors) {
        const el = document.querySelector(sel);
        if (el) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 500 && rect.height > 300) {
                contentEl = el;
                break;
            }
        }
    }

    if (contentEl) {
        contentEl.style.position = 'absolute';
        contentEl.style.left = '0';
        contentEl.style.top = '0';
        contentEl.style.width = '100%';
        contentEl.style.maxWidth = 'none';
        contentEl.style.height = '100%';
        contentEl.style.zIndex = '100';

        let scrollContainer = null;
        for (const sel of scrollContainerSelectors) {
            scrollContainer = contentEl.querySelector(sel);
            if (scrollContainer) break;
        }
        if (scrollContainer) {
            scrollContainer.style.position = 'absolute';
            scrollContainer.style.left = '0';
            scrollContainer.style.width = '100%';
        }
    }

    return { hiddenCount, contentEl: contentEl ? contentEl.className : null };
}
