const PICODOCS = {latest: "2.3.0", rootPlatform: "rp2040", versions: [{version: "2.3.0", platforms: ["rp2040","rp2350",]},{version: "2.2.0", platforms: ["rp2040","rp2350",]},{version: "2.1.1", platforms: ["rp2040","rp2350",]},{version: "2.1.0", platforms: ["rp2040","rp2350",]},{version: "2.0.0", platforms: ["rp2040","rp2350",]},{version: "1.5.1", platforms: ["rp2040",]},]};
(function () {
    const buildPath = window.location.pathname.match(/^\/(\d+\.\d+\.\d+)\/([a-z0-9-]+)\/(.*)$/);
    const current = buildPath
        ? {version: buildPath[1], platform: buildPath[2], page: buildPath[3]}
        : {version: PICODOCS.latest, platform: PICODOCS.rootPlatform, page: window.location.pathname.replace(/^\//, '')};

    if (!current.page) {
        current.page = 'index.html';
    }

    function goToBuild(build) {
        const base = '/' + build + '/';
        const page = base + current.page;
        fetch(page, {method: 'HEAD'}).then(function (response) {
            window.location.href = response.ok ? page + window.location.hash : base;
        }).catch(function () {
            window.location.href = base;
        });
    }

    function navElement() {
        const select = document.createElement('select');
        select.className = 'picodocs-nav-select';
        select.setAttribute('aria-label', 'SDK version and platform');

        PICODOCS.versions.forEach(function (entry) {
            const group = document.createElement('optgroup');
            group.label = entry.version === PICODOCS.latest ? entry.version + ' (latest)' : entry.version;
            entry.platforms.forEach(function (platform) {
                const option = document.createElement('option');
                option.value = entry.version + '/' + platform;
                option.textContent = entry.version + ' ' + platform.toUpperCase();
                group.appendChild(option);
            });
            select.appendChild(group);
        });

        select.value = current.version + '/' + current.platform;
        select.addEventListener('change', function () {
            goToBuild(select.value);
        });

        const wrapper = document.createElement('div');
        wrapper.className = 'picodocs-nav';
        wrapper.appendChild(select);
        return wrapper;
    }

    const logo = document.querySelector('#top .logo');
    const mobile = document.querySelector('.navigation-mobile');

    if (logo) {
        const label = logo.querySelector('span');
        if (label) {
            label.replaceWith(navElement());
        } else {
            logo.appendChild(navElement());
        }
    }

    if (mobile) {
        mobile.appendChild(navElement());
    }

    if (!logo && !mobile) {
        document.body.insertBefore(navElement(), document.body.firstChild);
    }
})();
