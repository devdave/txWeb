
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


function webchat_application() {
    /**
     * txWeb simple chat application
     *
     */
    const USER_SAYS = 1;
    const USER_JOINED = 2;
    const USER_LEFT = 3;

    var usernameInput = document.querySelector("input.username")
        , messageInput = document.querySelector("input.messagebox")
        , bodyDiv = document.querySelector("div.body")
        , listener = null;

    function tellServer(msg_code, message, on_success, on_fail) {

        post_ajax("/messageboard/tell",{"type":msg_code, "message":message})
            .addError((evt,xhr) => {
                console.debug(evt,xhr);
            })
            .addSuccess(response => {
                console.debug(response);

            })
            .go();

    }

    function sendRegister(username) {
        post_ajax("/messageboard/register", {"type":USER_JOINED,"username":username})
            .addSuccess(response=>{
                if(response['result'] == "OK") {
                    startListening();
                } else{
                    alert("Failed to register username");
                    console.error(response);
                }
            }).go()
    }

    function startListening() {
        listener = new EventSource("/messageboard/listen");

        listener.addEventListener("message", evt => {
            data = JSON.parse(evt.data)
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

            bodyDiv.append(div);
        });

    }

    function writeToBoard(type, message) {

    }

    function sendMessage() {
        let username = usernameInput.value,
            message = messageInput.value;

        if(message === "") {
            return;
        }

        tellServer(USER_SAYS, message);

        messageInput.value = "";
        messageInput.focus();

    }

    function send_on_enter(event) {
        if(event.code !== "Enter") {
            return;
        }
        sendMessage();
        console.debug("Enter key was pressed in message box");
    }


    function send_on_buttonclick(event) {
        sendMessage();
        console.debug("Send button was clicked");
    }

    function getUsername(){
        usernameInput.value = prompt("Please provide a username")
        sendRegister(usernameInput.value);
    }


    getUsername();

    document.querySelector(".messagebox").addEventListener("keyup", send_on_enter);
    document.querySelector(".send_msg").addEventListener("click", send_on_buttonclick);
    messageInput.focus()
    console.debug("Webchat is setup");

}

window.addEventListener("load", webchat_application);
console.debug("Waiting for document load")
