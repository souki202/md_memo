import getApiUrl from '/js/getApiUrl.js';
import getTheme from '/js/colorTheme.js';
import urlParameter from '/js/urlParameter.js';
import '/js/js.cookie.min.js';

axios.defaults.withCredentials = true;

const Loading = window.VueLoading;

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
            {{ memo.created_at }}
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
    components: {
        'loading': Loading
    },
    data: () => {
        return {
            errorMessage: '',
            memos: [],
            pinnedMemos: [],
            nextPageMemoId: '',
            memoAllCheck: false,

            isTrash: false,

            operationType: '',
            theme: 'light',

            // loading
            isLoading: false,
            fullPage: true
        }
    },
    mounted() {
        const place = urlParameter('place');

        if (place == 'trash') {
            this.isTrash = true;
            this.getTrashMemoList();
        }
        else {
            this.getMemoList();
            this.getPinnedMemoList();
        }

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
                console.log(res);
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

        getTrashMemoList() {
            axios.get(getApiUrl() + '/get_trash_memo_list').then((res) => {
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

        toTrashMemo(checkedMemoList) {
            // if (!window.confirm('ゴミ箱に移動するとシェアの設定が削除されます. よろしいですか?')) {
            //     return;
            // }
            axios.post(getApiUrl() + '/to_trash_memo', {
                params: {memo_id_list: checkedMemoList}
            }).then((res) => {
                console.log(res);
                location.reload();
            }).catch((err) => {
                console.log(err);
                this.errorMessage = 'メモの削除に失敗しました';
            }).then(() => {
                this.isLoading = false;
            })
        },

        /**
         * メモのソフトデリートを実行する
         */
        deleteMemo(checkedMemoList) {
            if (!window.confirm('ゴミ箱から削除したメモは復元できません。削除してよろしいですか?')) {
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
                this.isLoading = false;
            })
        },

        /**
         * メモをゴミ箱から戻す
         */
        restoreMemo(checkedMemoList) {
            axios.post(getApiUrl() + '/restore_memo', {
                params: {memo_id_list: checkedMemoList}
            }).then((res) => {
                console.log(res);
                location.reload();
            }).catch((err) => {
                console.log(err);
                this.errorMessage = 'メモの削除に失敗しました';
            }).then(() => {
                this.isLoading = false;
            })
        },

        memoOperation() {
            this.clearMessage()
            const checkedMemoList = this.getCheckMemoList();
            if (!checkedMemoList.length) {
                window.alert('メモが選択されていません');
                return;
            }

            if (checkedMemoList.length > 10) {
                window.alert('10件より多くの選択はできません');
                return; 
            }
            this.isLoading = true;
            switch (this.operationType) {
                case 'trash':
                    this.toTrashMemo(checkedMemoList);
                    break;
                case 'delete':
                    this.deleteMemo(checkedMemoList);
                    break;
                case 'restore':
                    this.restoreMemo(checkedMemoList);
                    break;
            }
            this.operationType  = '';
        }
    },
});