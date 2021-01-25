(function(mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
      mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
      define(["../../lib/codemirror"], mod);
    else // Plain browser env
      mod(CodeMirror);
  })(function(CodeMirror) {
    "use strict";
  
    var listRE = /^(\s*)(>[> ]*|[*+-] \[[x ]\]\s|[*+-]\s|(\d+)([.)]))(\s*)/,
        emptyListRE = /^(\s*)(>[> ]*|[*+-] \[[x ]\]|[*+-]|(\d+)[.)])(\s*)$/,
        unorderedListRE = /[*+-]\s/;

    CodeMirror.commands.newlineAndIndentToUnder = function (cm) {
        var sels = cm.listSelections();
        for (var i = sels.length - 1; i >= 0; i--) {
            const head = {
                line: sels[i].anchor.line,
                ch: cm.getLine(sels[i].anchor.line).length
            };
            const newHead = {
                line: sels[i].anchor.line + 1,
                ch: 0
            };
            cm.replaceRange(cm.doc.lineSeparator(), head, head, "+input");
            cm.setSelection(newHead, newHead);
        }
        sels = cm.listSelections();
        for (var i$1 = 0; i$1 < sels.length; i$1++)
            { cm.indentLine(sels[i$1].from().line, null, true); }
    };

    CodeMirror.commands.newlineAndIndentToAbove = function (cm) {
        var sels = cm.listSelections();
        for (var i = sels.length - 1; i >= 0; i--) {
            const head = {
                line: sels[i].anchor.line,
                ch: 0
            };
            const newHead = {
                line: sels[i].anchor.line,
                ch: 0
            };
            cm.replaceRange(cm.doc.lineSeparator(), head, head, "+input");
            cm.setSelection(newHead, newHead);
        }
        sels = cm.listSelections();
        for (var i$1 = 0; i$1 < sels.length; i$1++)
            { cm.indentLine(sels[i$1].from().line, null, true); }
    };
  
    CodeMirror.commands.newlineAndIndentContinueMarkdownListToUnder = function(cm) {
      if (cm.getOption("disableInput")) return CodeMirror.Pass;
      var ranges = cm.listSelections(), replacements = [];
      for (var i = 0; i < ranges.length; i++) {
        var pos = ranges[i].head;
  
        // If we're not in Markdown mode, fall back to normal newlineAndIndent
        var eolState = cm.getStateAfter(pos.line);
        var inner = CodeMirror.innerMode(cm.getMode(), eolState);
      }
    
    };
  
    // Auto-updating Markdown list numbers when a new item is added to the
    // middle of a list
    function incrementRemainingMarkdownListNumbers(cm, pos) {
      var startLine = pos.line, lookAhead = 0, skipCount = 0;
      var startItem = listRE.exec(cm.getLine(startLine)), startIndent = startItem[1];
  
      do {
        lookAhead += 1;
        var nextLineNumber = startLine + lookAhead;
        var nextLine = cm.getLine(nextLineNumber), nextItem = listRE.exec(nextLine);
  
        if (nextItem) {
          var nextIndent = nextItem[1];
          var newNumber = (parseInt(startItem[3], 10) + lookAhead - skipCount);
          var nextNumber = (parseInt(nextItem[3], 10)), itemNumber = nextNumber;
  
          if (startIndent === nextIndent && !isNaN(nextNumber)) {
            if (newNumber === nextNumber) itemNumber = nextNumber + 1;
            if (newNumber > nextNumber) itemNumber = newNumber + 1;
            cm.replaceRange(
              nextLine.replace(listRE, nextIndent + itemNumber + nextItem[4] + nextItem[5]),
            {
              line: nextLineNumber, ch: 0
            }, {
              line: nextLineNumber, ch: nextLine.length
            });
          } else {
            if (startIndent.length > nextIndent.length) return;
            // This doesn't run if the next line immediatley indents, as it is
            // not clear of the users intention (new indented item or same level)
            if ((startIndent.length < nextIndent.length) && (lookAhead === 1)) return;
            skipCount += 1;
          }
        }
      } while (nextItem);
    }
  });
  