import getApiUrl from '/js/getApiUrl.js'
import getTheme from '/js/colorTheme.js';

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
        axios.post(getApiUrl() + '/check_token', {}, {
            withCredentials: true
        }).then((res) => {
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
            }, {
                withCredentials: true
            }).then((res) => {
                const token = res.data.token
                Cookies.remove('session_token');
                if (this.form.rememberMe) {
                    Cookies.set('session_token', token, { domain: document.domain, expires: new Date('1 Jan 2037 00:00:00 GMT') });
                }
                else {
                    Cookies.set('session_token', token, { domain: document.domain });
                }
                console.log('success');
                location.href = '/home.html';
            }).catch((err) => {
                console.log(err)
                if (err.response.status == 401) {
                    this.errorMessage = "Wrong email or password"
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
            }, {
                withCredentials: true
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
