/**
 * A simple Ajax POST helper
 *
 * @param url
 * @param data
 * @returns {{addError: (function(*)), addSuccess: (function(*)), go: (function())}}
 */
function post_ajax(url, data){

    var xhr = new XMLHttpRequest(),
        handler = {
            addError:function(cb) {
                xhr.addEventListener("error",evt=>{
                    cb(evt, xhr);
                });
                return handler;
            }
            , addSuccess:function(cb) {
                xhr.addEventListener("load", evt=>{
                    if(xhr.readyState == xhr.DONE) {
                        cb(JSON.parse(xhr.responseText))
                    }
                });
                return handler;
            }
            , go: function() {
                xhr.open("POST", url);
                xhr.setRequestHeader("Content-Type", "application/json");
                xhr.send(JSON.stringify(data));
                return handler;
            }
        };

    return handler;

}

const ActionTypes = {
    RESET: "RESET"
    , MOVE: "MOVE"
}
    

const ResponseTypes = {
    OK: "OK"
    ,ERROR: "ERROR"
    ,WIN: "WIN"
    ,STALEMATE: "STALEMATE"
    ,RESET: "RESET"
    ,MOVE: "MOVE"

    // Details
    ,PLAYER: "player"
    ,CPU: "cpu"
    ,WTF: "WTF"
};


class T3Game {
    constructor(mapCellCls, playerCls, cpuCls) {
        console.log("Creating game", mapCellCls, playerCls, cpuCls);

        this.cells = document.getElementsByClassName(mapCellCls);
        for(let cell of this.cells){
            cell.addEventListener("click", this.onClick.bind(this));
        }

        this.mapCellCls = mapCellCls;
        this.playerCls = playerCls;
        this.cpuCls = cpuCls;

        this.tellServer(ActionTypes.RESET, null);
    }

    onClick(evt) {
        console.log("Caught click", evt);

        console.log(evt, evt.target, evt.target.dataset["cell"]);
        this.tellServer(ActionTypes.MOVE, evt.target.dataset["cell"]);
    }

    tellServer(command, detail) {
        console.log("Telling server", command, detail);

        post_ajax("/do", {"command": command, "detail": detail})
            .addSuccess(data=>{
                this.onSuccessResponse(data, detail)
            })
            .addError((evt, xhr) => {
                console.log("Error", evt, xhr);
            })
            .go();
    }

    onSuccessResponse(response, requestDetail) {
        let status = response['status']
            , state = response['state']
            , detail = response['detail'];

        console.log("Processing response", response, requestDetail);

        if (status != ResponseTypes.ERROR && status != ResponseTypes.RESET) {
            for(let cell of this.cells){
                if (cell.dataset[this.mapCellCls] == requestDetail ){
                    cell.classList.add(this.playerCls);
                }
            }
        }

        if (status === ResponseTypes.RESET) {
            for(let el of this.cells){
                el.className = this.mapCellCls;
            }
        }
        else if (status == ResponseTypes.MOVE) {
            for(let el of this.cells) {
                if(el.dataset["cell"] == detail) {
                    el.classList.add(this.cpuCls);
                }
            }
        }
        else if (status == ResponseTypes.WIN) {
            let who = state;
            if (who == ResponseTypes.CPU) {
                for(let cell of this.cells) {
                    if (cell.dataset["cell"] == detail) {
                        if (who == ResponseTypes.CPU) {
                            cell.classList.add(this.cpuCls);
                        } else {
                            cell.classList.add(this.playerCls);
                        }
                    }
                }
            }
            alert(`${who} has won`);
            this.tellServer(ResponseTypes.RESET, null);
        } else if (status == ResponseTypes.STALEMATE) {
            alert("Game stale mated");
            this.tellServer(ResponseTypes.RESET, null);
        }

    }
}

var game = null;

window.addEventListener("load", evt => {
    game = new T3Game("cell", "player", "cpu");
})