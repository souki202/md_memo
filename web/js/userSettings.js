import getApiUrl from '/js/getApiUrl.js'
import urlParameter from '/js/urlParameter.js';
import getTheme from '/js/colorTheme.js';

new Vue({
    el: '#userSettings',
    data: () => {
        return {
            errorMessage: '',
            successMessage: '',

            form: {
                basic: {
                    email: '',
                    password: '',
                    newPassword: '',
                    confirmNewPassword: '',
                }
            },
            theme: 'light',
        }
    },
    mounted() {
        this.theme = getTheme();
        this.getUserData();
    },
    methods: {
        getUserData() {
            axios.get(getApiUrl() + '/get_user_data', {
                withCredentials: true
            }).then((res) => {
                console.log(res);
                const userId = res.data.user.user_id;
                this.form.basic.email = userId;
                this.userViewName = userId.substring(0, userId.indexOf('@'));
            }).catch((err) => {
                console.log(err);
                this.userViewName = 'エラーが発生しました'
            }).then(() => {
                // always executed
            })
        },
        updateUserData() {
            this.successMessage = '';
            this.errorMessage = '';

            axios.post(getApiUrl() + '/update_user_data', {
                params: this.form.basic
            }, {
                withCredentials: true
            }).then((res) => {
                console.log(res);
                this.successMessage = '更新しました';
            }).catch((err) => {
                console.log(err.response);
                if (err.response.status == 401) {
                    this.errorMessage = '認証に失敗しました';
                }
                else {
                    this.errorMessage = '更新に失敗しました';
                }
            }).then(() => {
                // always executed
            })
            return false;
        },
        switchTheme() {
            Cookies.set('theme', this.theme, {expires: new Date('1 Jan 2037 00:00:00 GMT')});
            console.log("update theme.: " + this.theme);
            location.reload();
        }
    },
});