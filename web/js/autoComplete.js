export default class {
    constructor(sourceId, targetId) {
        this.db = [];
        this.exclude = [];

        this.recommends = [];

        this.selected = null;

        this.sourceId = sourceId;
        this.targetId = targetId;

        this.autocomplete = document.getElementById(sourceId);
        this.autocomplete_result = document.getElementById(targetId);
                
        // this.autocomplete.addEventListener("keyup", (e) => {this.updPopup(e)});
        // this.autocomplete.addEventListener("change", (e) => {this.updPopup(e)});
        // this.autocomplete.addEventListener("focus", (e) => {this.updPopup(e)});
    }

    clearRecommends() {
        this.recommends = [];
    }

    updateRecommendList() {
        const searchText = this.autocomplete.value;
        this.clearRecommends();
        if(!searchText) {
            this.clearRecommends();
            return;
        }
        this.db.forEach((e) => {
            if (e.indexOf(searchText) >= 0) {
                if (this.exclude[e]) {
                    return;
                }
                this.recommends.push(e);
            }
        });
    }

    updPopup(event) {
        console.log(event);
        if(!this.autocomplete.value) {
            this.clearRecommends();
            return;
        }
        const key = event.key;
        // 非表示にするキーなので出さないように
        if (key == 'Escape') {
            return;
        }
        const searchText = this.autocomplete.value;
        let fragment = document.createDocumentFragment();
        let isShowResult = false;
        this.recommends = [];
        for(let x = 0; x < this.db.length; x++) {
            if(this.db[x].indexOf(searchText) >= 0) {
                // 検索除外リストに入っていれば除外
                // 多分ifの前よりこっちのほうが速い
                if (this.exclude[this.db[x]]) {
                    continue;
                }
                isShowResult = true;
                let d = document.createElement("p");
                d.innerText = this.db[x];
                this.recommends.push(this.db[x]);
                d.setAttribute("onclick", this.sourceId + ".value=this.innerText;" + this.targetId + ".innerHTML='';" + this.targetId + ".style.display='none';");
                fragment.appendChild(d);
            }
        }
        if(isShowResult == true) {
        //     this.autocomplete_result.innerHTML = "";
        //     this.autocomplete_result.style.display = "block";
        //     this.autocomplete_result.appendChild(fragment);
            return;
        }
        this.popupClearAndHide();
    }

    setList(list) {
        this.db = list;
    }

    addExcludeWord(word) {
        this.exclude[word] = 1;
    }

    delExcludeWord(word) {
        delete this.exclude[word]
    }

    getRecommends() {
        return this.recommends;
    }
}
