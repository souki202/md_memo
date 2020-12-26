import getApiUrl from '/js/getApiUrl.js'
import '/js/js.cookie.min.js'
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
            }
        }
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
                    this.errorMessage = "そのユーザはすでに登録されています"
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
