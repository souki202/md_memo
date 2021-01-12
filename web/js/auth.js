import getApiUrl from '/js/getApiUrl.js'
import urlParameter from '/js/urlParameter.js';

const instance = axios.create({
    withCredentials: true
})

/**
 * userDataはwindowに代入しているためグローバル
 */

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
            instance.post(getApiUrl() + '/check_token').then((res) => {
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
            instance.post(getApiUrl() + '/logout').then(res => {
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

new Vue({
    el: "#sidebar",
    data: () => {
        return {
            userViewName: '',
            userGroupName: 'Free plan',
            userData: null,
        }
    },
    mounted() {
        const viewNameCache = Cookies.get('view_name_cache');
        if (viewNameCache) {
            this.userViewName = viewNameCache;
        }
        this.getUserData();
    },
    methods: {
        getUserData() {
            instance.get(getApiUrl() + '/get_user_data').then((res) => {
                console.log(res);
                this.userData = res.data.user;
                window.userData = res.data.user;
                const userId = res.data.user.user_id;
                this.userViewName = userId.substring(0, userId.indexOf('@'));
                Cookies.set('view_name_cache', this.userViewName, { domain: document.domain, expires: new Date('1 Jan 2037 00:00:00 GMT') });
            }).catch((err) => {
                console.log(err);
                this.userViewName = 'エラーが発生しました'
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
})