export class ChatClient {
    constructor(socket, chat_window, input, send_btn) {
        this.socket = socket;
        this.chat_window = document.getElementById(chat_window);
        this.input = document.getElementById(input);
        this.send = document.getElementById(send_btn);
        this.is_registered = false;

        this.send.addEventListener("click", this.on_chat.bind(this));
        this.socket.register("client.hear", this.provide_hear.bind(this));


    }

    async register() {
        if (this.is_registered == false) {
            const username = window.prompt("What is your username?", "Anonymous")
            const result = await this.socket.ask("chat.register", {username});
            this.is_registered = result
        }
    }

    async on_chat(evt) {
        const text = this.input.value;
        if(await this.socket.ask("chat.speak", {text}) == true) {
            this.input.value = "";
        }
        else {
            this.render_output("Client", "Failed to connect with server");
        }
    }

    async provide_hear({who, what}) {
        console.log("Got a message from server", who, what);
        this.render_output(who, what);
    }

    render_output(who, what) {
        const chat_line = `<span>${who}</span><span>${what}</span>`;
        const div_line = document.createElement("div")
        div_line.classList.add("text-msg");
        div_line.innerHTML = chat_line;

        this.chat_window.appendChild(div_line);
    }




}