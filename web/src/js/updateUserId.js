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
        axios.post(getApiUrl() + '/update_user_id', {
            params: {token: token},
        }, {
            withCredentials: true
        }).then(res => {
            console.log(res);
            location.href = '/user.html';
        }).catch(err => {
            console.log(err)
            this.errorMessage = 'ユーザIDの更新に失敗しました。お手数をおかけしますが、再度お試しください。'
        }).then(() => {

        })
    },
    methods: {

    }
})