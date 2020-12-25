import getApiUrl from '/js/getApiUrl.js'
import '/js/js.cookie.min.js'
// import '/js/axios.min.js';

new Vue({
    el: '#signupForm',
    data: () => {
        return {
            errorMessage: '',
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
                this.errorMessage = 'There are not enough input items.'
                return false;
            }

            if (password != password2) {
                this.errorMessage = 'Password input does not match.';
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
                const token = res.data.token
                Cookies.set('session_token', token, { domain: document.domain})
                location.href = "/home.html"
            }).catch((err) => {
                console.log(err.response.status)
                if (err.response.status == 403) {
                    this.errorMessage = "The user is already registered."
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
