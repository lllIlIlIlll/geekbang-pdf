/**
 * Find the main content container on the page.
 * Looks for scrollable containers with substantial content.
 */
function findContentContainer() {
    const selectors = [
        '[class*="article"]',
        '[class*="content"]',
        '[class*="article-content"]',
        '[class*="post-content"]',
        '[id*="article"]',
        '[id*="content"]',
        'main',
        'article',
        '.main-content'
    ];

    let contentContainer = null;
    let maxHeight = 0;

    document.querySelectorAll('div').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
            style.overflow === 'auto' || style.overflow === 'scroll') {
            const rect = el.getBoundingClientRect();
            const scrollHeight = el.scrollHeight;
            if (scrollHeight > maxHeight && rect.height > 500 &&
                !el.className.includes('sidebar') &&
                !el.className.includes('catalog') &&
                !el.className.includes('menu') &&
                !el.className.includes('nav')) {
                maxHeight = scrollHeight;
                contentContainer = el;
            }
        }
    });

    if (!contentContainer) {
        for (const selector of selectors) {
            const el = document.querySelector(selector);
            if (el) {
                const rect = el.getBoundingClientRect();
                const scrollHeight = el.scrollHeight;
                if (scrollHeight > 500 && rect.height > 500) {
                    contentContainer = el;
                    break;
                }
            }
        }
    }

    if (!contentContainer) {
        let maxScrollHeight = 0;
        document.body.querySelectorAll(':scope > div').forEach(el => {
            const scrollHeight = el.scrollHeight;
            const rect = el.getBoundingClientRect();
            if (scrollHeight > maxScrollHeight && rect.height > 500) {
                maxScrollHeight = scrollHeight;
                contentContainer = el;
            }
        });
    }

    if (contentContainer) {
        return {
            found: true,
            tagName: contentContainer.tagName,
            className: contentContainer.className,
            id: contentContainer.id,
            scrollHeight: contentContainer.scrollHeight,
            clientHeight: contentContainer.clientHeight,
            rectHeight: contentContainer.getBoundingClientRect().height
        };
    }

    return { found: false };
}
