function createSigninOptions() {
    const domain = document.domain

    switch (domain) {
        case 'localhost':
        case '127.0.0.1':
        case 'dev-md-memo.tori-blog.net':
            return [
                firebase.auth.GoogleAuthProvider.PROVIDER_ID,
                firebase.auth.FacebookAuthProvider.PROVIDER_ID,
                firebase.auth.TwitterAuthProvider.PROVIDER_ID,
                firebase.auth.GithubAuthProvider.PROVIDER_ID
            ];
        break;
        case 'stg-md-memo.tori-blog.net':
            return [];
        case 'md-memo.tori-blog.net':
            return [];
        default:
            return [];
        break;
    }
}

window.addEventListener('load', (e) => {
    // Your web app's Firebase configuration
    let firebaseConfig = {
        apiKey: "AIzaSyD6MLkcX67e8PuP_ahhViaKxfpfKs_n1J0",
        authDomain: "md-memo-dev.firebaseapp.com",
        projectId: "md-memo-dev",
        storageBucket: "md-memo-dev.appspot.com",
        messagingSenderId: "1027966385551",
        appId: "1:1027966385551:web:e14807689a8eea9e1c1ffa"
    };
    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);

    let ui = new firebaseui.auth.AuthUI(firebase.auth());
    ui.start('#firebaseuiAuthContainer', {
        signInOptions: createSigninOptions(),
        // Other config options...
    });
})