import getApiUrl from '/js/getApiUrl.js';
import '/js/js.cookie.min.js';

new Vue({
    el: '#homeMemoList',
    data: () => {
        return {
            errorMessage: '',
            memos: [],
            memoAllCheck: false,
        }
    },
    mounted() {
        axios.get(getApiUrl() + '/get_memo_list', {
            withCredentials: true
        }).then((res) => {
            for (let item of res.data.items) {
                item.checked = false;
                this.memos.push(item);
            }
        }).catch((err) => {
            console.log(err);
            this.errorMessage = 'Failed to get the memo list.';
        }).then(() => {
        })
    },
    methods: {
        switchAllCheck() {
            for (const i in this.memos) {
                this.$set(this.memos[i], 'checked', this.memoAllCheck)
            }
        }
    },
});