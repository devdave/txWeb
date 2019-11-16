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

const EventTypes = {
    USER_SAYS: 1
    , USER_JOINED: 2
    , USER_LEFT: 3
    , ERROR: 4
};

/**
 * Client for Message board
 *
 */
class WebChat {
    constructor(userInputCls, messageInputCls, bodyCls, sendButtonCls) {
        console.log("New Webchat client created");

        this.usernameInput = document.querySelector(userInputCls);
        this.messageInput = document.querySelector(messageInputCls);
        this.bodyDiv = document.querySelector(bodyCls);
        this.sendButton = document.querySelector(sendButtonCls);
        this.listener = null;
    }

    run() {
        console.log("Webchat client running");

        this.getUsername();
        this.messageInput.addEventListener("keyup", this.handleKeyUp.bind(this));
        this.sendButton.addEventListener("click", this.handleClick.bind(this));
        this.messageInput.focus();
    }

    getUsername(){
        console.log("getting username");

        this.usernameInput.value = prompt("Please provide a username")
        this.sendRegister(this.usernameInput.value);
    }

    sendRegister(username, on_success) {
        console.log(`Sending ${username} to server for registration`);

        post_ajax("/messageboard/register", {"type": EventTypes.USER_JOINED,"username":username})
            .addSuccess(response=>{
                if(response['result'] == "OK") {
                    this.startListening();
                } else{
                    alert(`Failed to register username\n${response['reason']}`);
                    console.error(response);
                    this.getUsername();
                }
            }).go()
    }

    startListening() {
        console.log("Starting to listen to messageboard for events");

        this.listener = new EventSource("/messageboard/listen");

        this.listener.addEventListener("message", evt => {

            let data = JSON.parse(evt.data)
            console.log(`SSE ${evt.data}`);
            this.onNewEvent(data);
        });

        this.listener.addEventListener("error", evt => {
            console.log(evt, this.listener);

            if(this.listener.readyState == this.listener.CLOSED) {
                this.onError({"reason": "Server listener disconnected"});
            } else {
                this.onError({"reason": "Unknown server listener error occurred"})
            }

            this.listener.close();
        })


    }

    printMessage(who, what){
        let timestamp = Date.now().toString();

        let newLineBody = `
            <span class="timestamp">${timestamp}</span>
            <span class="postedby">${who}</span>
            <span class="message">${what}</span>
        `;
        let div = document.createElement("div");
        div.classList.add("line");
        div.classList.add("error");
        div.innerHTML = newLineBody;
        this.bodyDiv.append(div);
        this.bodyDiv.scrollTop = this.bodyDiv.scrollHeight;
    }

    onError(data) {
        console.log(`Handling new error event ${JSON.stringify(data)}`);
        this.printMessage("Server", data.reason);
    }

    onNewEvent(data) {
        console.log(`Handling new server event ${JSON.stringify(data)}`);
        this.printMessage(data.username, data.message);
    }

    handleKeyUp(evt) {
        if(event.code !== "Enter") {
            return;
        }
        console.log("User pressed enter on message input");

        this.sendMessage();
    }

    handleClick(evt) {
        console.log("User pressed send button");

        this.sendMessage();
    }

    sendMessage() {
        let username = this.usernameInput.value,
            message = this.messageInput.value;

        if(message === "") {
            return;
        }


        this.tellServer(EventTypes.USER_SAYS, message);

        this.messageInput.value = "";
        this.messageInput.focus();
    }

    tellServer(msg_code, message) {
        console.log(`Telling server ${msg_code} ${message}`);

        post_ajax("/messageboard/tell",{"type":msg_code, "message":message})
            .addError((evt,xhr) => {
                console.log(evt,xhr);
            })
            .addSuccess(response => {
                console.log(response);
                //
                if(response.result == "ERROR") {
                    this.onError(response);
                } else {
                    //Ignore the response and assume everything is good
                }


            })
            .go();
    }


}

function main() {
    let chat = new WebChat("input.username"
        , "input.messagebox"
        , "div.body"
        , "button.send_msg"
    )
    chat.run()
}

window.addEventListener("load", main);
console.log("Waiting for document load")
