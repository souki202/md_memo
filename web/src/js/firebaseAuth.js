import getApiUrl from './getApiUrl.js'
import getEnv from './getEnv.js'
import './js.cookie.min.js'

function createSigninOptions() {
    const domain = document.domain

    switch (domain) {
        case 'localhost':
        case '127.0.0.1':
        case 'dev-md-memo.tori-blog.net':
            return [
                firebase.auth.GoogleAuthProvider.PROVIDER_ID,
                firebase.auth.FacebookAuthProvider.PROVIDER_ID,
                // firebase.auth.TwitterAuthProvider.PROVIDER_ID,
                firebase.auth.GithubAuthProvider.PROVIDER_ID
            ];
        break;
        case 'stg-md-memo.tori-blog.net':
            return [
                firebase.auth.GoogleAuthProvider.PROVIDER_ID,
                firebase.auth.FacebookAuthProvider.PROVIDER_ID,
                // firebase.auth.TwitterAuthProvider.PROVIDER_ID,
                firebase.auth.GithubAuthProvider.PROVIDER_ID
            ];
        case 'memo-ease.com':
            return [];
        default:
            return [];
        break;
    }
}

function getFireBaseConfig() {
    switch (getEnv()) {
        case 'dev':
        case 'stg':
            return {
                apiKey: "AIzaSyD6MLkcX67e8PuP_ahhViaKxfpfKs_n1J0",
                authDomain: "md-memo-dev.firebaseapp.com",
                projectId: "md-memo-dev",
                storageBucket: "md-memo-dev.appspot.com",
                messagingSenderId: "1027966385551",
                appId: "1:1027966385551:web:e14807689a8eea9e1c1ffa"
            };
        break;
        case 'prod':
        default:
            return [

            ];
        break;
    }
}

new Vue({
    el: '#firebaseApp',
    data: () => {
        return {
            errorMessage: '',
            authUi: null,
            uiConfig: null,
        }
    },
    mounted() {
        // Your web app's Firebase configuration
        let firebaseConfig = getFireBaseConfig();
        // Initialize Firebase
        firebase.initializeApp(firebaseConfig);

        const snsLoginMethod = this.executeSnsLogin;
        const outerthis = this
        this.authUi = new firebaseui.auth.AuthUI(firebase.auth());
        this.uiConfig = {
            callbacks: {
                signInSuccessWithAuthResult: function(authResult, redirectUrl) {
                    firebase.auth().currentUser.getIdToken(false).then(idToken => {
                        snsLoginMethod(idToken);
                    }).catch(function(err) {
                        console.log(err.response)
                        outerthis.errorMessage = '認証中にエラーが発生しました'
                    });

                    console.log(redirectUrl);
                    return false;
                },
                uiShown: function() {
                    // The widget is rendered.
                },
            },
            signInFlow: 'popup',
            signInSuccessUrl: '/google_ldogin.html',
            signInOptions: createSigninOptions(),
            tosUrl: '/terms_of_service.html',
            privacyPolicyUrl: '/privacy_policy.html'
        };
        firebase.auth().useDeviceLanguage();
        this.authUi.start('#firebaseuiAuthContainer', this.uiConfig);
    },
    methods: {
        executeSnsLogin(idToken) {
            axios.post(getApiUrl() + '/sns_login', {
                params: {
                    id_token: idToken,
                }
            }).then((res) => {
                console.log(res);
                const token = res.data.token
                Cookies.remove('session_token');
                Cookies.set('session_token', token, { domain: document.domain, expires: new Date('1 Jan 2037 00:00:00 GMT') });
                location.href = '/home.html';
            }).catch((err) => {
                console.log(err.response)
                console.log(err)
                if (err.response.data.registerd) {
                    this.errorMessage = 'すでに通常アカウントで登録済みです'
                }
                else {
                    this.errorMessage = '認証中にエラーが発生しました'
                }
            }).then(() => {
                // always executed
            })
        },
    },
})

window.addEventListener('load', (e) => {
})