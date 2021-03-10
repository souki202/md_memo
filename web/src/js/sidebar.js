(() => {
    document.getElementById("switchSidebar").addEventListener('change', (e) => {
        const isCheched = e.target.checked;
        if (isCheched) {
            mainDom.classList.add('sidebar-opened');
            mainDom.classList.remove('sidebar-closed');
        }
        else {
            mainDom.classList.remove('sidebar-opened');
            mainDom.classList.add('sidebar-closed');
        }
    });
})();