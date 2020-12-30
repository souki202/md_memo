import getApiUrl from '/js/getApiUrl.js';
import getTheme from '/js/colorTheme.js';
import '/js/js.cookie.min.js';

new Vue({
    el: '#homeMemoList',
    data: () => {
        return {
            errorMessage: '',
            memos: [],
            memoAllCheck: false,

            operationType: '',
            theme: 'light',
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

        // tableのカラーを設定
        this.theme = getTheme();
    },
    methods: {
        clearMessage() {
            this.errorMessage = '';
        },

        switchAllCheck() {
            for (const i in this.memos) {
                this.$set(this.memos[i], 'checked', this.memoAllCheck)
            }
        },

        /**
         * @returns {Array<string>} チェックされたメモのuuid一覧
         */
        getCheckMemoList() {
            let result = [];
            this.memos.forEach(e => {
                if (e.checked) result.push(e.uuid);
            });
            return result;
        },

        /**
         * メモのハードデリートを実行する
         */
        deleteMemo() {
            this.clearMessage()
            const checkedMemoList = this.getCheckMemoList();
            if (!checkedMemoList.length) {
                window.alert('メモが選択されていません');
                return;
            }

            if (!window.confirm('削除したメモは復元できません。よろしいですか?')) {
                return;
            }
            
            axios.post(getApiUrl() + '/delete_memo', {
                params: checkedMemoList
            }, {
                withCredentials: true
            }).then((res) => {
                console.log(res);
                location.reload();
            }).catch((err) => {
                console.log(err);
                this.errorMessage = 'メモの削除に失敗しました';
            }).then(() => {
            })
        },

        /**
         * メモのソフトデリートを実行する
         */
        moveToGarbageMemo() {
            this.clearMessage()
            const checkedMemoList = this.getCheckMemoList();
            if (!checkedMemoList.length) {
                window.alert('メモが選択されていません');
                return;
            }
        },

        memoOperation() {
            switch (this.operationType) {
                case 'del':
                    this.deleteMemo();
                    break;
            }
            this.operationType  = '';
        }
    },
});