(function(mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
      mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
      define(["../../lib/codemirror"], mod);
    else // Plain browser env
      mod(CodeMirror);
  })(function(CodeMirror) {
    "use strict";

    CodeMirror.commands.addMultiCursorUp = function (cm) {
        addMultiCursor(cm, -1);
    };

    CodeMirror.commands.addMultiCursorDown = function (cm) {
        addMultiCursor(cm, 1);
    };

    function addMultiCursor(cm, direction) {
        if (direction == 0) return;

        const sels = cm.listSelections();
        for (let sel of sels) {
            // 単一のカーソルの場合
            if (sel.head.line == sel.anchor.line && sel.head.ch == sel.anchor.ch) {
                const head = sel.head
                // 1行目より上には指定できないので終了
                if (head.line + direction < 0) {
                    continue;
                }
                let newCursor = {
                    line: head.line + direction,
                    ch: Math.min(cm.getLine(head.line).length, head.ch)
                }
                cm.addSelection(newCursor, newCursor);
            }
            else { // 選択の場合
                let frontCursor = null;
                let endCursor = null;
                let newCursor = null;
                if (sel.head.line < sel.anchor.line
                    || (sel.head.line == sel.anchor.line && sel.head.ch < sel.anchor.ch)) {
                    frontCursor = sel.head;
                    endCursor = sel.anchor;
                }
                else {
                    frontCursor = sel.anchor;
                    endCursor = sel.head;
                }

                if (direction < 0) {
                    if (frontCursor.line == 0) {
                        newCursor = {
                            line: frontCursor.line,
                            ch: 0
                        };
                    }
                    else {
                        newCursor = {
                            line: frontCursor.line - 1,
                            ch: Math.min(frontCursor.ch, cm.getLine(frontCursor.line).length)
                        };
                    }
                    cm.addSelection(newCursor, frontCursor);
                }
                else {
                    if (endCursor.line == cm.lineCount() - 1) {
                        newCursor = {
                            line: cm.lineCount() - 1,
                            ch: Math.max(endCursor.ch, cm.getLine(endCursor.line).length)
                        };
                    }
                    else {
                        newCursor = {
                            line: endCursor.line + 1,
                            ch: Math.min(endCursor.ch, cm.getLine(endCursor.line).length)
                        };
                    }
                    cm.addSelection(endCursor, newCursor);
                }
            }
        }
    };
});