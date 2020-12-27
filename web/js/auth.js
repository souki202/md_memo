import getApiUrl from '/js/getApiUrl.js'
import urlParameter from '/js/urlParameter.js';

new Vue({
    el: '#header',
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
                // シェアされたメモを見る場合は, 非ログイン状態でも見れる設定があるので確認
                const shareId = urlParameter('share_id');
                // セッション切れやその他エラーはログイン画面へ
                console.log(err);
                if (!shareId) {
                    console.log(shareId)
                    location.href = '/login.html';
                }
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