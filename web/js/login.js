import getApiUrl from '/js/getApiUrl.js'
import getTheme from '/js/colorTheme.js';

axios.defaults.withCredentials = true;

new Vue({
    el: '#loginForm',
    data: () => {
        return {
            errorMessage: '',
            successMessage: '',
            form: {
                email: '',
                password: '',
                rememberMe: false,
            },
            isLogin: false,
            theme: 'light',
        }
    },
    mounted() {
        this.theme = getTheme();
        // ログイン済みならhomeへ
        axios.post(getApiUrl() + '/check_token').then((res) => {
            location.href = '/home.html'
        }).catch((err) => {
        }).then(() => {
            // always executed
        })
    },
    methods: {
        clearMessage() {
            this.errorMessage = ''
            this.successMessage = ''
        },
        submit() {
            this.clearMessage();
            
            const email = this.form.email;
            const password = this.form.password;

            if (!email || !password) {
                this.errorMessage = 'メールアドレスとパスワードを入力してください'
                // this.errorMessage = 'There are not enough input items.'
                return false;
            }

            axios.post(getApiUrl() + '/login', {
                params: {
                    email: email,
                    password: password,
                }
            }).then((res) => {
                const token = res.data.token
                Cookies.remove('session_token');
                if (this.form.rememberMe) {
                    Cookies.set('session_token', token, { domain: document.domain, expires: new Date('1 Jan 2037 00:00:00 GMT') });
                }
                else {
                    Cookies.set('session_token', token, { domain: document.domain });
                }
                Cookies.set('did_use', '1', { domain: document.domain, expires: new Date('1 Jan 2037 00:00:00 GMT') });
                console.log('success');
                location.href = '/home.html';
            }).catch((err) => {
                console.log(err.response)
                if (err.response.status == 401) {
                    console.log(err.response.data)
                    if (err.response.data.limit_try_login) {
                        this.errorMessage = "しばらく時間をおいてからログインをしてください"
                    }
                    else {
                        this.errorMessage = "Emailまたはパスワードが異なります."
                    }
                }
                else {
                    this.errorMessage = "Unknown error"
                }
            }).then(() => {
                // always executed
            })
            return false;
        },

        resetPassword() {
            this.clearMessage();
            const email = this.form.email;
            if (!email) {
                this.errorMessage = 'メールアドレスを入力してください'
                return false;
            }

            axios.post(getApiUrl() + '/reset_password', {
                params: {
                    email: email,
                }
            }).then((res) => {
                const token = res.data.token
                this.successMessage = 'パスワードリセット用メールを送信しました'
            }).catch((err) => {
                console.log(err)
                this.errorMessage = 'パスワードリセット用メールの送信に失敗しました'
            }).then(() => {
                // always executed
            })
        }
    },
})
