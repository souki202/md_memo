export default class {
    constructor(sourceId, targetId) {
        this.db = [];

        this.sourceId = sourceId;
        this.targetId = targetId;

        this.autocomplete = document.getElementById(sourceId);
        this.autocomplete_result = document.getElementById(targetId);
                
        this.autocomplete.addEventListener("keyup", (e) => {this.updPopup()});
        this.autocomplete.addEventListener("change", (e) => {this.updPopup()});
        this.autocomplete.addEventListener("focus", (e) => {this.updPopup()});
    }

    popupClearAndHide() {
        this.autocomplete_result.innerHTML = "";
        this.autocomplete_result.style.display = "none";
    }

    updPopup() {
        if(!this.autocomplete.value) {
            this.popupClearAndHide();
            return;
        }
        let a = new RegExp("^" + this.autocomplete.value, "i");
        let fragment = document.createDocumentFragment();
        let isShowResult = false;
        for(let x = 0; x < this.db.length; x++) {
            if(a.test(this.db[x])) {
                isShowResult = true;
                let d = document.createElement("p");
                d.innerText = this.db[x];
                d.setAttribute("onclick", this.sourceId + ".value=this.innerText;" + this.targetId + ".innerHTML='';" + this.targetId + ".style.display='none';");
                fragment.appendChild(d);
            }
        }
        if(isShowResult == true) {
            this.autocomplete_result.innerHTML = "";
            this.autocomplete_result.style.display = "block";
            this.autocomplete_result.appendChild(fragment);
            return;
        }
        this.popupClearAndHide();
    }

    setList(list) {
        this.db = list
    }
}
