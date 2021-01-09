import getApiUrl from '/js/getApiUrl.js'

axios.defaults.withCredentials = true;

new Vue({
    el: '#headerMenuNav',
    data: () => {
        return {
            isLogin: false,
        }
    },
    mounted() {
        this.checkLoggedIn();
    },
    methods: {
        checkLoggedIn() {
            // 一度も使用していないユーザならAPIは叩かない
            const didUse = Cookies.get('did_use');
            if (!didUse) {
                return;
            }
            axios.post(getApiUrl() + '/check_token').then((res) => {
                console.log('token check success');
                this.isLogin = true;
            }).catch((err) => {
            }).then(() => {
                // always executed
            })
        },
        logout() {
            axios.post(getApiUrl() + '/logout').then(res => {
                console.log('success logout');
            }).catch(err => {
                console.log('failed to logout on server.');
            }).then(() => {
                Cookies.remove('session_token');
                location.href = '/login.html';                
            })
        }
    }
});