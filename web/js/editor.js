import getApiUrl from '/js/getApiUrl.js'
import getFileApiUrl from '/js/getFileApiUrl.js'
import getTheme from '/js/colorTheme.js';
import getEnv from '/js/getEnv.js';
import urlParameter from '/js/urlParameter.js';
import autoComplete from '/js/autoComplete.js';
import '/codemirror/lib/codemirror.js';
import '/js/js.cookie.min.js';
import '/js/uuidv4.min.js';
import CodeMirrorHelper from '/js/memoHelper.js';

axios.defaults.withCredentials = true;

class ShareTypes {
    static DoNotShare = 1;
    static Readonly = 2;
    static Editable = 4;
}

class PinnedTypes {
    static NoPinned = 1;
    static Pinned = 2;
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
            setTags: [],
            allTags: [],
            tagAutoComplete: null,

            viewModes: new ViewModes(ViewModes.ModeList.Normal),
            updatePreviewTimeout: null,
            autoSaveTimeout: null,
            autoSaveDelay: 5000,

            codemriror: null,
            codemirrorHelper: null,

            showMessageTime: 3000,
            isShowShareDialog: false,

            isSharedView: false,

            theme: 'light',

            memoMessages: [],

            isSaving: false,
            canSave: true,
            saveInterval: 10000,
        }
    },
    computed: {
        shareUrl() {
            if (!this.memo.share.id) {
                return '';
            }

            const domain = document.domain;
            return 'https://' + domain + '/' + 'memo.html?share_id=' + this.memo.share.id;
        },
    },
    mounted() {
        this.tagAutoComplete = new autoComplete('tagInputArea', 'tagRecommendation');

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
            autofocus: true,
            dragDrop: false,
            extraKeys: {"Enter": "newlineAndIndentContinueMarkdownList"},
        });
        // body変更時の挙動設定
        this.codemirror.on('change', () => {
            this.memo.body = this.codemirror.getValue();
            this.updatePreview();

            if (this.autoSaveTimeout) clearTimeout(this.autoSaveTimeout);
            this.autoSaveTimeout = setTimeout(this._save, this.autoSaveDelay);
        })
        // this.codemirror.on('drop', (data, e) => {
        //     console.log(e);
        //     let files = e.dataTransfer.files;
        //     // this.uploadFile(editor, e)
        // })
        this.codemirrorHelper = new CodeMirrorHelper(this.codemirror);

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

        // tagを取得
        this.getAllTags();
    },
    methods: {
        /**
         * メモを保存する
         */
        _save() {
            if (!this.canSave || !window.userData) {
                return;
            }

            // シェア画面で編集権限がないとき
            if (this.isSharedView && this.memo.share.type != 4) {
                console.log(memo);
                return;
            }

            this.errorMessage = '';
            if (this.memo.body.length > this.getMaxBodyLen()) {
                this.errorMessage = 'メモの上限文字数は' + this.getMaxBodyLen() + '文字です'
                return;
            }

            // 保存処理
            this.isSaving = true;
            this.canSave = false;
            axios.post(getApiUrl() + '/save_memo', {
                params: {
                    memo: this.memo,
                    files: this.getFileKeys(),
                }
            }).then(res => {
                console.log('auto save complete: ' + res.data.id);
                this.memo.id = res.data.id
                this.drawMessage('saved');
            }).catch(err => {
                console.log(err);
                this.errorMessage = 'Failed to update memo.'
            }).then(() => {
                this.isSaving = false;
            })

            // 一定時間保存できないように
            setTimeout(() => {
                this.canSave = true
            }, this.saveInterval);
        },

        save() {
            if (this.autoSaveTimeout) clearTimeout(this.autoSaveTimeout);
            this._save();
        },

        getMaxBodyLen() {
            const userData = window.userData;
            if (!userData) {
                return 10000;
            }
            else if (userData.plan == 1) {
                return 10000;
            }
            else if (userData.plan >= 1000) {
                return 100000;
            }
            else {
                return 10000;
            }
        },

        getFileKeys() {
            let apiUrl = getFileApiUrl();
            let r = /a/
            switch (getEnv()) {
                case 'dev':
                    r = /https:\/\/fileapi\.dev-md-memo\.tori-blog\.net\/get_file\/\?file_key=([\w_\-%]+)/g;
                    break;
                case 'stg':
                    r = /https:\/\/fileapi\.stg-md-memo\.tori-blog\.net\/get_file\/\?file_key=([\w_\-%]+)/g;
                    break;
                case 'prod':
                    r = /https:\/\/fileapi\.memo-ease\.com\/get_file\/\?file_key=([\w_\-%]+)/g;
                    break;
                default:
                    r = /https:\/\/fileapi\.memo-ease\.com\/get_file\/\?file_key=([\w_\-%]+)/g;
                    break;
            }
            let m = null;
            var a = [];
            while ((m = r.exec(this.memo.body)) != null) {
                a.push(m[1]);
            }
            
            console.log(a);
            return a;
        },

        getAllTags() {
            axios.get(getApiUrl() + '/get_tags').then(res => {
                console.log(res.data);
                this.tagAutoComplete.setList([
                    
                ]);

            }).catch(err => {
                console.log(err);
                this.errorMessage = 'Failed to get tags.';
            }).then(() => {
            });
        },

        setMemoData(memo) {
            let newMemoData = {}
            newMemoData.id = memo.uuid;
            newMemoData.title = memo.title;
            newMemoData.description = memo.description;
            newMemoData.type = memo.memo_type;
            newMemoData.body = memo.body;
            newMemoData.share = {
                type: 1,
                scope: 1,
                id: '',
                users: '',
            };
            if (memo.share) {
                newMemoData.share.id = memo.share.share_id;
                newMemoData.share.type = memo.share.share_type;
                newMemoData.share.scope = memo.share.share_scope;
                newMemoData.share.users = memo.share.share_users;
            }
            if (!memo.pinned_type) {
                newMemoData.pinnedType
            }
            else {
                newMemoData.pinnedType = memo.pinned_type
            }
            this.$set(this, 'memo', newMemoData);
            this.codemirror.setValue(this.memo.body);
            this.updatePreviewCallback();
        },

        /**
         * メモを読み込む
         */
        load() {
            if (this.memo.id) {
                axios.get(getApiUrl() + '/get_memo_data', {
                    params: {memo_id: this.memo.id},
                }).then(res => {
                    console.log(res.data)
                    this.setMemoData(res.data.memo);
                }).catch(err => {
                    console.log(err);
                    this.errorMessage = 'Failed to load memo data.';
                }).then(() => {
                });
            }
        },

        loadByShareId(shareId) {
            if (shareId) {
                axios.get(getApiUrl() + '/get_memo_data_by_share_id', {
                    params: {share_id: shareId},
                }).then(res => {
                    console.log(res.data)
                    
                    this.setMemoData(res.data.memo);

                    // リードオンリーの場合はプレビュー表示が初期状態
                    if (this.memo.share.type == ShareTypes.Readonly) {
                        this.viewModes.setMode(ViewModes.ModeList.Preview);
                    }
                }).catch(err => {
                    console.log(err);
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
         * 通常はupdatePreviewが呼び出す. 即時実行されるため, そのときに呼んでも良い
         * TODO: rename refactoring
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
            }).then(res => {
                this.memo.share.id = res.data.share_id;
                console.log(res);
            }).catch(err => {
                this.errorMessage = 'シェア設定の変更に失敗しました';
                console.log(err);
            }).then(() => {

            });
            return false;
        },

        switchViewMode() {
            this.viewModes.switchMode();
        },

        switchPinned() {
            axios.post(getApiUrl() + '/switch_pinned', {
                params: {
                    id: this.memo.id,
                }
            }).then(res => {
                console.log(res.data)
                this.$set(this.memo, 'pinnedType', res.data.pinned_type)
                console.log(this.memo.pinnedType == 2);
            }).catch(err => {
                this.errorMessage = 'ピン留め設定の変更に失敗しました';
                console.log(err);
            }).then(() => {

            });
            return false;
        },

        createUploadTmpKey(){
            const LENGTH = 8 //生成したい文字列の長さ
            const SOURCE = "abcdefghijklmnopqrstuvwxyz0123456789" //元になる文字
            let result = ''
          
            for(let i=0; i<LENGTH; i++){
              result += SOURCE[Math.floor(Math.random() * SOURCE.length)];
            }
            
            return result
        },

        uploadFileBySignedUrl(file, url, key, tmpKey) {
            var reader = new FileReader();
            reader.readAsArrayBuffer(file);

            reader.onload = () => {
                axios({
                    method: 'PUT',
                    url: url,
                    headers: {
                        'Content-Type': file.type
                    },
                    data: reader.result
                }).then(res => {
                    console.log(res);                
                }).catch(err => {
                    console.log(err);
                    this.errorMessage = 'アップロードに失敗しました'
                    this.invokeCodemirrorOperation('uploadFailed', tmpKey);
                }).then(() => {
    
                })
            };
        },

        uploadFile(e) {
            let files = [...e.dataTransfer.files];
            if (files.length == 0) {
                return;
            }

            files.forEach(file => {
                let tmpKey = file.name.replace(/[\[\]\!]/g, '_');
                // アップロード中の文字列を追加
                this.invokeCodemirrorOperation('uploadFile', tmpKey)

                if (file.size > 1024*1024*8) {
                    this.errorMessage = '8MBまでアップロード可能です'
                    return false;
                }

                // 署名付きURLを取得し, 成功したらそこにアップロード
                axios.post(getApiUrl() + '/create_upload_url', {
                    params: {
                        fileName: file.name,
                        fileSize: file.size
                    }
                }).then(res => {
                    console.log(res);
                    const key = res.data.key;
                    const url = res.data.url;
                    console.log('upload url: ' + key)
                    // アップ完了の文字置換
                    this.invokeCodemirrorOperation('uploadComplete', tmpKey, key);
                    // 反映のため, 即保存
                    this.save();

                    // 画像本体アップ
                    this.uploadFileBySignedUrl(file, url, key, tmpKey);
                }).catch(err => {
                    console.log(err);
                    this.errorMessage = 'アップロード用URLの取得に失敗しました'
                    this.invokeCodemirrorOperation('uploadFailed', tmpKey);
                }).then(() => {

                })
            });
        },

        invokeCodemirrorOperation(op, ...args) {
            return this.codemirrorHelper.invoke(op, ...args);
        },
    },
})