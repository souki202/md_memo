export default class {
    constructor(codemirror) {
        this.codemirror = codemirror;
    }

    invoke(op, ...args) {
        switch (op) {
            case 'bold':
                this.bold(args);
                break;
            case 'italic':
                this.italic(args);
                break;
            case 'debug':
                this.debug(args);
        }
    }

    bold() {
        const selections = this.codemirror.getSelections();
        const replaced = selections.map(s => {
            // すでにboldだったら解除する
            if (s.length > 4 && s.indexOf('**') == 0 && s.indexOf('**', s.length - 2) != -1) {
                return s.substring(2, s.length - 2);
            }
            return '**' + s + '**'
        });
        this.codemirror.replaceSelections(replaced, 'around');
    }

    italic() {
        const selections = this.codemirror.getSelections();
        const replaced = selections.map(s => {
            // すでにitalicだったら解除する
            if (s.length > 2 && s.indexOf('*') == 0 && s.indexOf('*', s.length - 1) != -1) {
                return s.substring(1, s.length - 1);
            }
            return '*' + s + '*'
        });
        this.codemirror.replaceSelections(replaced, 'around');
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
}