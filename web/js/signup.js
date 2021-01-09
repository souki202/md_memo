import getApiUrl from '/js/getApiUrl.js'
import '/js/js.cookie.min.js'
import getTheme from '/js/colorTheme.js';
// import '/js/axios.min.js';

new Vue({
    el: '#signupForm',
    data: () => {
        return {
            errorMessage: '',
            successMessage: '',
            form: {
                email: '',
                password: '',
                password2: '',
            },
            theme: 'light',
        }
    },
    mounted() {
        this.theme = getTheme();
    },
    methods: {
        submit() {
            this.errorMessage = "";

            const email = this.form.email;
            const password = this.form.password;
            const password2 = this.form.password2;

            if (!email || !password || !password2) {
                // this.errorMessage = 'There are not enough input items.'
                this.errorMessage = '入力が不足しています'
                return false;
            }

            if (password.length < 8) {
                this.errorMessage = 'パスワードは8文字以上入力してください';
                return false;
            }

            if (password != password2) {
                // this.errorMessage = 'Password input does not match.';
                this.errorMessage = '確認用のパスワードが一致しません';
                return false;
            }
            axios.post(getApiUrl() + '/signup', {
                params: {
                    email: email,
                    password: password,
                }
            }, {
                withCredentials: true
            }).then((res) => {
                this.successMessage = '本登録用のメールを送信しました';
            }).catch((err) => {
                console.log(err.response.status)
                if (err.response.status == 403) {
                    this.errorMessage = "そのユーザはすでに登録されているか、退会済みのユーザです。"
                }
                else {
                    this.errorMessage = "サーバーエラーが発生しました"
                }
            }).then(() => {
                // always executed
            })
            return false;
        }
    },
})

// window.onSignIn = function(googleUser) {
//     var idToken = googleUser.getAuthResponse().id_token;

//     axios.post(getApiUrl() + '/google_login', {
//         params: {
//             id_token: idToken,
//         }
//     }).then((res) => {
//         console.log(res);
//         // this.successMessage = '本登録用のメールを送信しました';
//     }).catch((err) => {
//         console.log(err)
        
//     }).then(() => {
//         // always executed
//     })
// }