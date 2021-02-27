import getApiUrl from './getApiUrl.js'
import urlParameter from './urlParameter.js';

new Vue({
    el: '#app',
    data: () => {
        return {
            errorMessage: ''
        }
    },
    mounted() {
        const token = urlParameter('token');
        axios.post(getApiUrl() + '/regist_complete', {
            token: token,
        }, {
            withCredentials: true
        }).then(res => {
            const token = res.data.token;
            Cookies.set('session_token', token, { domain: document.domain, expires: new Date('1 Jan 2037 00:00:00 GMT') });
            location.href = '/home.html';
        }).catch(err => {
            this.errorMessage = '本登録の処理に失敗しました.'
        }).then(() => {

        })
    },
    methods: {

    }
})