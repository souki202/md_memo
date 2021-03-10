import getApiUrl from './getApiUrl.js';
import getEnv from './getEnv.js';
import urlParameter from './urlParameter.js';
import getTheme from './colorTheme.js';
import memoListItemComponent from './memoListItemComponent.vue';
import './js.cookie.min.js';
import {createApp} from 'vue/dist/vue.esm-bundler.js';

axios.defaults.withCredentials = true;

Vue.component('memo-card', memoListItemComponent)

createApp({
    data() {
        return {
            errorMessage: '',
            allTags: [],
            matchMemos: [],
            tagSearchValue: '',
            activeTag: '',
            theme: 'light',
            nextPageMemoId: null
        }
    },
    mounted() {
        this.theme = getTheme();
        this.getAllTags();
    },
    methods: {
        getAllTags() {
            this.errorMessage = '';
            axios.get(getApiUrl() + '/get_tags').then(res => {
                console.log(res.data);
                this.allTags = res.data.tags;
            }).catch(err => {
                console.log(err);
                this.$parent.errorMessage = 'タグの取得に失敗しました';
            }).then(() => {
            });
        },

        /**
         * 新規にタグを作成する
         * 
         * @param {string} newTag 新しいタグ 
         */
        createNewTag(newTag) {
            this.errorMessage = '';
            console.log(newTag);
            if (newTag.length > 50) {
                this.$parent.errorMessage = 'タグの名前の長さは50文字までです';
                return false;
            }
            axios.post(getApiUrl() + '/update_tag', {
                params: {
                    name: newTag,
                }
            }).then(res => {
                const newTagData = {
                    uuid: res.data.id,
                    name: newTag,
                }
                this.allTags.push(newTagData);
            }).catch(err => {
                console.log(err);
                this.$parent.errorMessage = 'タグの追加に失敗しました';
            }).then(() => {
            });
        },

        searchMemoByTag(tagUuid) {
            console.log(tagUuid);
            this.errorMessage = '';
            this.matchMemos.splice(0, this.matchMemos.length);
            this.activeTag = tagUuid;
            this.nextPageMemoId = null;
            this.addMemoList(tagUuid);
        },

        addMemoList() {
            axios.get(getApiUrl() + '/search_memo_by_tag', {
                params: {
                    uuid: this.activeTag,
                    next_page_memo_id: this.nextPageMemoId
                }
            }).then((res) => {
                console.log(res);
                if (res.data.items) {
                    this.matchMemos = this.matchMemos.concat(res.data.items.filter(v => !!v));
                }
                this.nextPageMemoId = res.data.next_page_memo_id;
            }).catch((err) => {
                console.log(err);
                this.errorMessage = 'メモの検索に失敗しました'
            }).then(() => {

            });
        },

        deleteTag(tagUuid) {
            this.errorMessage = '';
            axios.post(getApiUrl() + '/delete_tag', {
                params: {
                    uuid: tagUuid
                }
            }).then((res) => {
                console.log(res);
                location.reload();
            }).catch((err) => {
                console.log(err);
                this.errorMessage = 'タグの削除に失敗しました'
            }).then(() => {

            });
        }
    }
}).mount('#tagManager');