import getApiUrl from '/js/getApiUrl.js'
import getTheme from '/js/colorTheme.js';
import urlParameter from '/js/urlParameter.js';
import '/codemirror/lib/codemirror.js';
import '/js/js.cookie.min.js';
import '/js/uuidv4.min.js';

class ShareTypes {
    static DoNotShare = 1
    static Readonly = 2
    static Editable = 4
}

class ViewModes {
    static ModeList = {
        Normal: 0,
        Source: 1,
        Preview: 2,
    }

    constructor(mode) {
        this.modeDescriptions = ['Normal', 'Source', 'Preview'];
        this.nowMode = mode;
        if (this.nowMode < 0 || this.nowMode >= this.modeDescriptions.length) {
            this.nowMode = 0;
        }
    }

    switchMode() {
        this.nowMode++;
        if (this.nowMode >= this.modeDescriptions.length) {
            this.nowMode = 0;
        }
    }

    setMode(mode) {
        this.nowMode = mode;
        if (this.nowMode < 0 || this.nowMode >= this.modeDescriptions.length) {
            this.nowMode = 0;
        }
    }

    get mode() {
        return this.nowMode;
    }

    get modeDescription() {
        this.modeDescription[this.nowMode];
    }
}

new Vue({
    el: '#memoEditor',
    data: () => {
        return {
            errorMessage: '',
            types: [
                'plain',
                'markdown',
            ],
            shareTypes: [
                {id: ShareTypes.DoNotShare, description: 'Do not share'},
                {id: ShareTypes.Readonly, description: 'Read only'},
                // {id: 3, description: 'Commentable'},
                {id: ShareTypes.Editable, description: 'Editable'},
            ],
            shareScopeTypes: [
                {id: 1, description: 'Public'},
                {id: 2, description: 'Specific Users'},
            ],
            memo: {
                id: '', // 編集時のみ
                title: 'No title',
                description: '',
                body: '',
                type: 1, // markdown
                share: {
                    type: 1,
                    scope: 1,
                    id: '',
                    users: '',
                },
            },

            viewModes: new ViewModes(ViewModes.ModeList.Normal),
            updatePreviewTimeout: null,
            autoSaveTimeout: null,
            autoSaveDelay: 5000,
            codemriror: null,
            showMessageTime: 3000,

            isShowShareDialog: false,

            isSharedView: false,

            theme: 'light',

            memoMessages: [],
        }
    },
    computed: {
        shareUrl() {
            if (!this.memo.share.id) {
                return '';
            }

            const domain = document.domain;
            let baseUrl = '';
            if (domain == 'dev-md-memo.tori-blog.net') {
                baseUrl = 'http://dev-md-memo.tori-blog.net/';
            }
            else {
                baseUrl = 'https://' + domain + '/';
            }
            return baseUrl + 'memo.html?share_id=' + this.memo.share.id;
        },
    },
    mounted() {
        // まずテーマ取得
        this.theme = getTheme();

        // codemirrorの適用
        this.codemirror = CodeMirror.fromTextArea(document.getElementById('memoBodyTextarea'), {
            mode: 'markdown',
            lineNumber: true,
            indentUnit: 4,
            theme: this.theme == 'light' ? 'mdn-like' : 'darcula',
            lineNumbers: true,
            autoCloseBrackets: true,
            scrollbarStyle: "simple",
            keyMap: 'default',
            historyEventDelay: 300,
            extraKeys: {"Enter": "newlineAndIndentContinueMarkdownList"},
        });
        // body変更時の挙動設定
        this.codemirror.on('change', () => {
            this.memo.body = this.codemirror.getValue();
            this.updatePreview();

            if (this.autoSaveTimeout) clearTimeout(this.autoSaveTimeout);
            this.autoSaveTimeout = setTimeout(this.save, this.autoSaveDelay);
        })

        // memo idを取得
        const memoId = urlParameter('memo_id');
        const shareId = urlParameter('share_id');
        if (memoId) {
            this.memo.id = memoId;
            this.load();
        }
        else if (shareId) {
            this.isSharedView = true;
            this.loadByShareId(shareId);
        }

        // markedの設定
        marked.setOptions({
            langPrefix: '',
            highlight: function (code, lang) {
                return hljs.highlightAuto(code, [lang]).value
            }
        });
    },
    methods: {
        /**
         * メモを保存する
         */
        save() {
            axios.post(getApiUrl() + '/save_memo', {params: this.memo}, {
                withCredentials: true
            }).then(res => {
                console.log('auto save complete: ' + res.data.id);
                this.memo.id = res.data.id
                this.drawMessage('saved');
            }).catch(err => {
                this.errorMessage = 'Failed to update memo.'
            }).then(() => {
            })
        },

        /**
         * メモを読み込む
         */
        load() {
            if (this.memo.id) {
                axios.get(getApiUrl() + '/get_memo_data', {
                    params: {memo_id: this.memo.id},
                    withCredentials: true
                }).then(res => {
                    const memo = res.data.memo;
                    this.memo.id = memo.uuid;
                    this.memo.title = memo.title;
                    this.memo.description = memo.description;
                    this.memo.tyoe = memo.memo_type;
                    this.memo.body = memo.body;
                    this.memo.share.id = memo.share.share_id;
                    this.memo.share.type = memo.share.share_type;
                    this.memo.share.scope = memo.share.share_scope;
                    this.memo.share.users = memo.share.share_users;
                    this.codemirror.setValue(this.memo.body);
                    this.updatePreviewCallback();
                }).catch(err => {
                    this.errorMessage = 'Failed to load memo data.';
                }).then(() => {
                });
            }
        },

        loadByShareId(shareId) {
            if (shareId) {
                axios.get(getApiUrl() + '/get_memo_data_by_share_id', {
                    params: {share_id: shareId},
                    withCredentials: true
                }).then(res => {
                    console.log(res.data)
                    const memo = res.data.memo;
                    this.memo.id = memo.uuid;
                    this.memo.title = memo.title;
                    this.memo.description = memo.description;
                    this.memo.type = memo.memo_type;
                    this.memo.body = memo.body;
                    this.memo.share.id = memo.share.share_id;
                    this.memo.share.type = memo.share.share_type;
                    this.memo.share.scope = memo.share.share_scope;
                    this.memo.share.users = memo.share.share_users;
                    this.codemirror.setValue(this.memo.body);

                    // リードオンリーの場合はプレビュー表示が初期状態
                    if (this.memo.share.type == ShareTypes.Readonly) {
                        this.viewModes.setMode(ViewModes.ModeList.Preview);
                    }
                    this.updatePreviewCallback();
                }).catch(err => {
                    console.log(res.data)
                    this.errorMessage = 'Failed to load memo data.';
                }).then(() => {
                });
            }
        },

        /**
         * markdownのプレビューを更新する
         */
        updatePreview() {
            if (this.updatePreviewTimeout) {
                clearTimeout(this.updatePreviewTimeout);
            }
            this.updatePreviewTimeout = setTimeout(this.updatePreviewCallback, 300);
        },

        /**
         * updatePreviewが呼び出す
         */
        updatePreviewCallback() {
            document.getElementById('memoBodyPreview').innerHTML = marked(this.memo.body)
            this.updatePreviewTimeout = null;
        },

        /**
         * メモ画面にメッセージを表示する
         * 
         * @param {string} message 表示するメッセージ 
         */
        drawMessage(message) {
            console.log('draw message: ' + message);
            const uuid = uuidv4();
            this.memoMessages.push({uuid: uuid, message: message});
            setTimeout(()=>{this.deleteMessage(uuid)}, this.showMessageTime);
        },

        /**
         * メッセージを削除する
         * 
         * @param {string} uuid 削除するメッセージのuuid 
         */
        deleteMessage(uuid) {
            const delIdx = this.memoMessages.findIndex(e => e.uuid == uuid);
            if (delIdx >= 0) {
                this.memoMessages.splice(delIdx, 1);
            }
        },

        /**
         * シェア機能のダイアログ表示
         */
        showShareDialog() {
            this.isShowShareDialog = true;
        },

        closeDialog() {
            this.isShowShareDialog = false;
        },

        /**
         * 共有リンクをクリップボードにコピー
         */
        copyShareUrl() {
            var copyText = document.querySelector("#shareLink");
            copyText.select();
            document.execCommand("copy");
        },

        /**
         * 共有リンクを現在の設定で更新する
         */
        updateShareLink() {
            axios.post(getApiUrl() + '/update_share_settings', {
                params: {
                    id: this.memo.id,
                    share: this.memo.share,
                }
            }, {
                withCredentials: true
            }).then(res => {
                this.memo.share.id = res.data.share_id;
                console.log(res);
            }).catch(err => {
                this.errorMessage = 'Failed to save share settings.';
                console.log(err);
            }).then(() => {

            });
            return false;
        },

        switchViewMode() {
            this.viewModes.switchMode();
        },
    },
})