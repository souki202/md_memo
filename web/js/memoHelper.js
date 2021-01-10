import getApiUrl from '/js/getApiUrl.js'
export default class {
    constructor(codemirror) {
        this.codemirror = codemirror;
    }

    invoke(op, ...args) {
        let result = null;
        switch (op) {
            case 'bold':
                result = this.bold(args);
                break;
            case 'italic':
                result = this.italic(args);
                break;
            case 'deleteText':
                result = this.deleteText(args);
                break;
            case 'header':
                result = this.header(args);
                break;
            case 'singleLineCode':
                result = this.singleLineCode();
                break;
            case 'multiLineCode':
                result = this.multiLineCode();
                break;
            case 'unorderdList':
                result = this.unorderdList();
                break;
            case 'orderdList':
                result = this.orderdList();
                break;
            case 'addIndent':
                result = this.addIndent();
                break;
            case 'addQuote':
                result = this.addQuote();
                break;
            case 'hr':
                result = this.hr();
                break;
            case 'link':
                result = this.link();
                break;
            case 'uploadFile':
                result = this.uploadFile(...args);
                break;
            case 'uploadComplete':
                result = this.uploadComplete(...args);
                break;
            case 'uploadFailed':
                result = this.uploadFailed(...args);
                break;
            case 'debug':
                result = this.debug(...args);
                break;
        }

        this.finalize();
        return result;
    }

    bold() {
        this.addTextAround('**');
    }

    italic() {
        this.addTextAround('*');
    }

    deleteText() {
        this.addTextAround('~~');
    }

    header(...args) {
        if (args.length == 0) return;
        const level = parseInt(args[0]);
        const h = '#'.repeat(level) + ' ';
        this.addTextHead(h);
    }

    singleLineCode() {
        this.addTextAround('`');
    }

    multiLineCode() {
        this.addTextAround('\n```\n');
    }

    unorderdList() {
        this.addTextHead('* ');
    }

    orderdList() {
        this.addTextHead('1. ');
    }

    addIndent() {
        this.addTextHead('    ');
    }

    addQuote() {
        this.addTextHeadEachLine('> ');
    }

    hr() {
        this.addTextHead('\n---\n\n');
    }

    link() {
        const selections = this.codemirror.getSelections();
        const replaced = selections.map(s => {
            // 選択文字列がhttp...
            if (s.match('^https?://.*')) {
                return '[リンク文字](' + s + ')';
            }
            else { // 選択文字がリンクでない
                return '[' + s + '](https://...)';
            }
        });
        this.codemirror.replaceSelections(replaced, 'around');
    }

    createFileUploadingText(tmpKey) {
        return '![Uploading ' + tmpKey + '...]()';
    }

    uploadFile(tmpKey) {
        this.replaceSelectionText(this.createFileUploadingText(tmpKey));
    }

    uploadComplete(tmpKey, file_key) {
        console.log('![' + tmpKey + '](https://' + getApiUrl() +  '/get_file/?file_key=' + file_key + ')');
        this.replaceSearchText(this.createFileUploadingText(tmpKey), '![' + tmpKey + '](' + getApiUrl() +  '/get_file/?file_key=' + file_key + ')');
    }

    uploadFailed(tmpKey) {
        this.replaceSearchText(this.createFileUploadingText(tmpKey), '![Failed to upload ' + tmpKey + '...]()');
    }

    /**
     * 選択中のテキストの前後に文字を挿入する
     * @param {string} addCh 挿入する文字
     */
    addTextAround(addCh) {
        const selections = this.codemirror.getSelections();
        const replaced = selections.map(s => {
            // すでにその状態だったら解除する
            if (s.length >= addCh.length * 2 && s.indexOf(addCh) == 0 && s.indexOf(addCh, s.length - addCh.length) != -1) {
                return s.substring(addCh.length, s.length - addCh.length);
            }
            return addCh + s + addCh
        });
        this.codemirror.replaceSelections(replaced, 'around');
    }

    /**
     * 選択中の行の行頭に文字を挿入する
     * @param {string} addCh 挿入する文字
     */
    addTextHead(addCh) {
        const selections = this.codemirror.listSelections();
        selections.forEach(e => {
            const head = {
                line: e.anchor.line,
                ch: 0
            };
            this.codemirror.replaceRange(addCh, head, head);
        });
    }

    addTextHeadEachLine(addCh) {
        const selections = this.codemirror.listSelections();
        selections.forEach(e => {
            const lineRange = {
                start: e.anchor.line,
                end: e.head.line,
            }
            for (let i = lineRange.start; i <= lineRange.end; i++) {
                const head = {
                    line: i,
                    ch: 0
                };
                this.codemirror.replaceRange(addCh, head, head);
            }
        });
    }

    /**
     * 選択中のテキストを置換する
     * @param {*} addCh 
     */
    replaceSelectionText(addCh) {
        this.codemirror.replaceSelection(addCh, 'around');
    }

    /**
     * 検索に一致するテキストを置換する
     * 
     * @param {str} serachText 
     * @param {str} newText 
     */
    replaceSearchText(serachText, newText) {
        let cursor = this.codemirror.getSearchCursor(serachText);
        while (cursor.findNext()) {
            cursor.replace(newText)
        }
    }

    debug() {
        let nowSelections = this.codemirror.listSelections();
        nowSelections.forEach(e => {
            console.log(e);
            let anchor = e.anchor;
            let head = e.head;
            anchor.ch = 1;
            head.ch = 5;
        });
        this.codemirror.setSelections(nowSelections);
    }

    finalize() {
        this.codemirror.focus();
    }
}