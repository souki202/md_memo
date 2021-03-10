import getApiUrl from './getApiUrl.js'
import urlParameter from './urlParameter.js';
import {createApp} from 'vue/dist/vue.esm-bundler.js';

createApp({
    data: () => {
        return {
            errorMessage: ''
        }
    },
    mounted() {
        const token = urlParameter('token');
        axios.post(getApiUrl() + '/execute_reset_password', {
            params: {token: token},
        }, {
            withCredentials: true
        }).then(res => {
            console.log(res);
            // location.href = '/login.html';
        }).catch(err => {
            console.log(err)
            this.errorMessage = 'パスワードリセットの処理に失敗しました.'
        }).then(() => {

        })
    },
    methods: {

    }
}).mount('#app');
