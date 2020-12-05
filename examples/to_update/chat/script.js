/**
 * A simple Ajax POST helper
 *
 * @param url
 * @param data
 * @returns {{addError: (function(*)), addSuccess: (function(*)), go: (function())}}
 */
async function post_ajax(url, data){

    return new Promise((resolve,reject)=>{
        var xhr = new XMLHttpRequest();
        xhr.onerror = function(evt){
            reject(evt, xhr);
        }

        xhr.onload = function(evt) {
            if(xhr.readyState == xhr.DONE) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(evt, xhr);
            }
        }

        xhr.open("POST", url);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify(data));
    })

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

    async sendRegister(username, on_success) {
        console.log(`Sending ${username} to server for registration`);

        try {
            let response = await post_ajax(
                "/messageboard/register",
                {"type": EventTypes.USER_JOINED,"username":username}
                )
            if(response['result'] == "OK") {
                this.startListening();
            } else {
                alert(`Failed to register username\n${response['reason']}`);
                console.error(response);
                this.getUsername();
            }
        } catch (e) {
            alert(`Failed to register: ${e}`);
            console.log(e);
        }

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

    async sendMessage() {
        let username = this.usernameInput.value,
            message = this.messageInput.value;

        if(message === "") {
            return;
        }


        await this.tellServer(EventTypes.USER_SAYS, message);

        this.messageInput.value = "";
        this.messageInput.focus();
    }

    async tellServer(msg_code, message) {
        console.log(`Telling server ${msg_code} ${message}`);

        try {
            let response = await post_ajax("/messageboard/tell",{"type":msg_code, "message":message});
            console.log(response);
            if(response.result == "ERROR") {
                this.onError(response);
            } else {
                //Assume everything is good
            }
        } catch(e) {
            console.log(e);
        }
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


console.log("Waiting for document load")
window.addEventListener("load", main);
