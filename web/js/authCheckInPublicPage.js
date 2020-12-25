import getApiUrl from '/js/getApiUrl.js'

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
            axios.post(getApiUrl() + '/check_token', {}, {
                withCredentials: true
            }).then((res) => {
                console.log('token check success');
                this.isLogin = true;
            }).catch((err) => {
            }).then(() => {
                // always executed
            })
        },
        logout() {
            axios.post(getApiUrl() + '/logout', {}, {
                withCredentials: true
            }).then(res => {
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