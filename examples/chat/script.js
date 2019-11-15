
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

class WebChat {
    constructor(userInputCls, messageInputCls, bodyCls, sendButtonCls) {
        console.debug("New Webchat client created");

        this.usernameInput = document.querySelector(userInputCls);
        this.messageInput = document.querySelector(messageInputCls);
        this.bodyDiv = document.querySelector(bodyCls);
        this.sendButton = document.querySelector(sendButtonCls);
        this.listener = null;
    }

    run() {
        console.debug("Webchat client running");

        this.getUsername();
        this.messageInput.addEventListener("keyup", this.handleKeyUp.bind(this));
        this.sendButton.addEventListener("click", this.handleClick.bind(this));
        this.messageInput.focus();
    }

    getUsername(){
        console.debug("getting username");

        this.usernameInput.value = prompt("Please provide a username")
        this.sendRegister(this.usernameInput.value);
    }

    sendRegister(username, on_success) {
        console.debug(`Sending ${username} to server for registration`);

        post_ajax("/messageboard/register", {"type": EventTypes.USER_JOINED,"username":username})
            .addSuccess(response=>{
                if(response['result'] == "OK") {
                    this.startListening();
                } else{
                    alert("Failed to register username");
                    console.error(response);
                }
            }).go()
    }

    startListening() {
        console.debug("Starting to listen to messageboard for events");

        this.listener = new EventSource("/messageboard/listen");

        this.listener.addEventListener("message", evt => {
            this.onNewEvent(JSON.parse(evt.data));
        });

    }

    onNewEvent(data) {
        console.debug(`Handling new server event ${JSON.stringify(data)}`);

        let newLineBody = `                
                    <span class="timestamp">
                        12345
                    </span>
                    <span class="postedby">
                        ${data.username}
                    </span>
                    <span class="message">
                        ${data.message}
                    </span>                            
        `
        let div = document.createElement("div");
        div.classList.add("line");
        div.innerHTML = newLineBody;

        this.bodyDiv.append(div);
    }

    handleKeyUp(evt) {
        if(event.code !== "Enter") {
            return;
        }
        console.debug("User pressed enter on message input");

        this.sendMessage();
    }

    handleClick(evt) {
        console.debug("User pressed send button");

        this.sendMessage();
    }

    sendMessage() {
        let username = this.usernameInput.value,
            message = this.messageInput.value;

        if(message === "") {
            return;
        }


        this.tellServer(EventTypes.USER_SAYS, message);

        messageInput.value = "";
        messageInput.focus();
    }

    tellServer(msg_code, message) {
        console.debug(`Telling server ${msg_code} ${message}`);

        post_ajax("/messageboard/tell",{"type":msg_code, "message":message})
            .addError((evt,xhr) => {
                console.debug(evt,xhr);
            })
            .addSuccess(response => {
                console.debug(response);
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
console.debug("Waiting for document load")
