import getApiUrl from '/js/getApiUrl.js';
import getEnv from '/js/getEnv.js';
import urlParameter from '/js/urlParameter.js';
import getTheme from '/js/colorTheme.js';
import memoListItemComponent from '/js/memoListItemComponent.js';
import '/js/js.cookie.min.js';

axios.defaults.withCredentials = true;

Vue.component('memo-card', memoListItemComponent)

new Vue({
    el: '#tagManager',
    data() {
        return {
            errorMessage: '',
            allTags: [],
            matchMemos: [],
            tagSearchValue: '',
            theme: 'light',
        }
    },
    mounted() {
        this.theme = getTheme();
        this.getAllTags();
    },
    methods: {
        getAllTags() {
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
            axios.get(getApiUrl() + '/search_memo_by_tag', {
                params: {
                    uuid: tagUuid
                }
            }).then((res) => {
                console.log(res);
                this.matchMemos = res.data.items;
            }).catch((err) => {
                console.log(err);
            }).then(() => {

            });
        },
    }
});