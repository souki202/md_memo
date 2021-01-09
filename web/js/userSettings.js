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
            userData: {
                has_password: true,
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
                this.userData = res.data.user;
                const userId = res.data.user.user_id;
                this.form.basic.email = userId;
                console.log(this.userData.has_password)
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

            if (this.userData.has_password && this.form.basic.password == '') {
                this.errorMessage = 'Emailと現在のパスワードは必須です'
                return;
            }
            if (this.form.basic.email == '') {
                this.errorMessage = 'Emailは必須です'
                return;
            }
            if (this.form.basic.newPassword != this.form.basic.confirmNewPassword) {
                this.errorMessage = '確認用のパスワードが一致しません'
                return;
            }

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

        withdrawal() {
            if (!window.confirm('退会すると、現在ご利用中のデータはご利用できなくなります。本当に退会しますか?')) {
                return;
            }
            axios.post(getApiUrl() + '/withdrawal', {}, {
                withCredentials: true
            }).then((res) => {
                window.alert('本サービスをご利用いただき、誠にありがとうございました。')
                Cookies.remove('session_token');
                location.href = '/';
                console.log(res);
            }).catch((err) => {
            }).then(() => {
                // always executed
            })
        },

        switchTheme() {
            Cookies.set('theme', this.theme, {expires: new Date('1 Jan 2037 00:00:00 GMT')});
            console.log("update theme.: " + this.theme);
            location.reload();
        }
    },
});