import getApiUrl from '/js/getApiUrl.js';
import getTheme from '/js/colorTheme.js';
import '/js/js.cookie.min.js';

axios.defaults.withCredentials = true;

Vue.component('memo-card', {
    template: `
    <div class="memo-card all-memo-item">
        <!-- メモ選択のチェックボックス -->
        <div class="form-group memo-check-button-container">
            <div class="custom-control custom-checkbox">
                <input type="checkbox" class="custom-control-input" :id="'memoCheck'+listType+memo.uuid" v-model="memo.checked">
                <label class="custom-control-label" :for="'memoCheck' + listType + memo.uuid"></label>
            </div>
        </div>

        <!-- その他情報 -->
        <div class="memo-title-container">
            <div class="memo-title">
                <a :href="'/memo.html?memo_id=' + memo.uuid" class="memo-list-link">{{ memo.title }}</a>
            </div>
        </div>
        <div class="memo-updated-at">
            {{ memo.updated_at }}
        </div>
    </div>
    `,

    data: () => {
        return {
            memo: {},
            listType: '',
        }
    },

    props: ['memo', 'listType'],
})

new Vue({
    el: '#homeMemoList',
    data: () => {
        return {
            errorMessage: '',
            memos: [],
            pinnedMemos: [],
            nextPageMemoId: '',
            memoAllCheck: false,

            operationType: '',
            theme: 'light',
        }
    },
    mounted() {
        this.getMemoList();
        this.getPinnedMemoList();

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

        getMemoList() {
            axios.get(getApiUrl() + '/get_memo_list').then((res) => {
                for (let item of res.data.items) {
                    item.checked = false;
                    this.memos.push(item);
                }
                this.nextPageMemoId = res.data.next_page_memo_id;
            }).catch((err) => {
                console.log(err);
                this.errorMessage = 'メモ一覧の取得に失敗しました';
            }).then(() => {
            })
        },

        addMemoList() {
            if (this.nextPageMemoId) {
                const params = {next_page_memo_id: this.nextPageMemoId};
                axios.get(getApiUrl() + '/get_memo_list', {params: params}).then((res) => {
                    for (let item of res.data.items) {
                        item.checked = false;
                        this.memos.push(item);
                    }
                    this.nextPageMemoId = res.data.next_page_memo_id;
                }).catch((err) => {
                    console.log(err);
                    this.errorMessage = 'メモ一覧の取得に失敗しました';
                }).then(() => {
                })
            }
        },

        getPinnedMemoList() {
            axios.get(getApiUrl() + '/get_pinned_memo_list').then((res) => {
                console.log(res);
                for (let item of res.data.items) {
                    item.checked = false;
                    this.pinnedMemos.push(item);
                }
            }).catch((err) => {
                console.log(err);
                this.errorMessage = 'Failed to get the memo list.';
            }).then(() => {
            })
        },

        /**
         * @returns {Array<string>} チェックされたメモのuuid一覧
         */
        getCheckMemoList() {
            let result = [];
            this.memos.forEach(e => {
                if (e.checked) result.push(e.uuid);
            });
            this.pinnedMemos.forEach(e => {
                if (e.checked) result.push(e.uuid);
            });
            // 重複消去
            result.filter(function (x, i, self) {
                return self.indexOf(x) === i;
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

            if (checkedMemoList.length > 25) {
                window.alert('25件より多くの選択はできません');
                return; 
            }

            if (!window.confirm('削除したメモは復元できません。よろしいですか?')) {
                return;
            }
            
            axios.post(getApiUrl() + '/delete_memo', {
                params: {memo_id_list: checkedMemoList}
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