import getApiUrl from '/js/getApiUrl.js'
// import '/js/axios.min.js';

new Vue({
    el: '#loginForm',
    data: () => {
        return {
            errorMessage: '',
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
        submit() {
            this.errorMessage = "";
            
            const email = this.form.email;
            const password = this.form.password;

            if (!email || !password) {
                this.errorMessage = 'There are not enough input items.'
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
                    Cookies.set('session_token', token, { domain: document.domain, expires: 9999 });
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
        }
    },
})
