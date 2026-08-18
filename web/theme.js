(function () {
    const footer = document.querySelector('.navigation-footer');
    if (!footer) {
        return;
    }

    const logo = footer.querySelector('img');
    if (logo) {
        logo.src = '/picodocs-logo.svg';
        logo.alt = 'Pinout.xyz';
    }

    const link = footer.querySelector('a');
    if (link) {
        link.href = 'https://github.com/pinout-xyz/picodocs';
        link.textContent = 'PicoDocs on GitHub';
    }
})();
