(function () {
    const popup_ids = ['MSearchResultsWindow', 'MSearchSelectWindow'];

    function apply(popup, property, value) {
        if (popup.style.getPropertyValue(property) !== value ||
            popup.style.getPropertyPriority(property) !== 'important') {
            popup.style.setProperty(property, value, 'important');
        }
    }

    function place() {
        const field = document.getElementById('MSearchField') || document.getElementById('MSearchBox');
        if (!field) {
            return;
        }

        const field_rect = field.getBoundingClientRect();
        if (!field_rect.width) {
            return;
        }

        const viewport_width = document.documentElement.clientWidth;
        const viewport_height = document.documentElement.clientHeight;
        const top = Math.round(field_rect.bottom + 2);
        const width = Math.min(300, viewport_width - 16);
        const left = Math.round(Math.max(8, Math.min(field_rect.left, viewport_width - width - 8)));
        const height = Math.min(400, viewport_height - top - 8);

        popup_ids.forEach(function (id) {
            const popup = document.getElementById(id);
            if (!popup || popup.style.display === 'none') {
                return;
            }

            apply(popup, 'top', top + 'px');
            apply(popup, 'left', left + 'px');

            if (id === 'MSearchResultsWindow') {
                apply(popup, 'width', width + 'px');
                apply(popup, 'height', height + 'px');
            }
        });
    }

    new MutationObserver(place).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['style'],
        subtree: true
    });

    window.addEventListener('resize', place);
})();
