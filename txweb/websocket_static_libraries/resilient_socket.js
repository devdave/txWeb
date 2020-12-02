
export {ResilientSocket};
import {Deferred} from "./deferred.js";


async function sleep(time) {
    return new Promise(resolve => {
        window.setTimeout(resolve, time);
    })
}


class ResilientSocket {
    constructor(conString, {debug=false} = {}) {
        this.conString = conString;
        this.closed = true;
        this.socket = null;
        this.callerID = 0;
        this.pending = {};

        //misc flags
        this.debug = debug;

        this.retries = 0;  //handled on server side firewall but to keep the client from freezing, limit it on this side
        this.retryLimit = 3;


        this.endpoints = {};

        this.connect();
    }

    async connect() {

        if(this.retries > this.retryLimit) {
            console.error("Number of connect retries reached limit!");
            // TODO add a on_timeout or on_limit hook so the application can handle
            // connection retries failing.
        }

        if(this.debug){
            console.debug("connecting resilient");
        }

        this.socket = new WebSocket(this.conString);
        this.socket.addEventListener("message", this.receiveMsg.bind(this));
        this.socket.addEventListener("close", this.onclose.bind(this));
        this.socket.addEventListener("open", this.onopen.bind(this));
        this.socket.addEventListener("error", this.onerror.bind(this));

        return new Promise((resolve, reject)=>{
            const self = this;
            async function on_open(evt){
                if(self.debug){
                    console.debug("Connection opened!", self.socket.readyState);
                }

                if(self.socket.readyState != self.socket.OPEN) {
                    await sleep(1000);
                }
                self.retries = 0;
                self.closed = false;
                self.socket.removeEventListener("open", this);
                self.socket.removeEventListener("error", on_error);
                resolve(evt);
            }

            function on_error(evt) {
                self.closed = true;
                self.socket.removeEventListener("error", this);
                reject(evt);
            }

            this.socket.addEventListener("open", on_open, {once: true});
            this.socket.addEventListener("error", on_error, {once: true});



        });

    }

    onopen() {
        console.log("rs.onopen called");
        this.closed = false;
        this.retries = 0;
    }

    onclose() {
        this.closed = true;
    }

    onerror(evt) {
        console.log(evt);
        this.retries += 1;

    }

    first_open(handler) {
        this.socket.addEventListener("open", handler, {once:true});
    }

    async _sendRaw(msg) {
        //Check if disconnected

        if(this.socket.readyState != this.socket.OPEN) {
            const result = await this.connect();
            console.log("this.connect", result, this.socket.readyState);
            this.socket.send(msg);
        } else {
            this.socket.send(msg);
        }

        if(this.debug){
            console.debug("Sent", msg);
        }



    }

    async sendMsg(endpoint, args) {
        let msg = {type:"tell", endpoint:endpoint, args: args};
        this._sendRaw(JSON.stringify(msg));
    }

    async sendResponse(caller_id, result){
        let msg = {type:"response", caller_id:caller_id, result:result}
        this._sendRaw(JSON.stringify(msg));
    }

    async receiveMsg(msg) {
        if(this.debug) {
            console.debug("received", msg);
        }

        let data = JSON.parse(msg.data);
        if (data['type'] == "response") {
            let d = this.pending[data['caller_id']];
            delete this.pending[data['caller_id']];
            d.fire(data.result);

        }
        else if(data['type'] == "tell") {
            if (this.endpoints[data['endpoint']] != undefined) {
                const endpoint = this.endpoints[data['endpoint']];
                await endpoint(data.args);
            } else {
                console.error(`Tell the user that ${data['endpoint']} doesn't exist`, data);
            }
        } else if(data['type'] == "ask") {
            if(this.endpoints[data['endpoint']] != undefined) {
                const endpoint = this.endpoints[data['endpoint']];
                let result = await endpoint(data.args);
                await this.sendResponse(data['caller_id'], result);
            } else{
                console.error(`User asked for ${data['endpoint']} that doesn't exist`, data);
            }

        } else {
            console.error("unhandled message", data);
        }
    }

    async ask(endpoint, args) {
        /**
         * Expects a response using Deferred for callbacks
         */
        console.debug("Asking", endpoint);

        let d = new Deferred()
        this.callerID += 1;
        this.pending[this.callerID] = d;

        let msg = {type:"ask", endpoint:endpoint, args: args, caller_id: this.callerID};
        this._sendRaw(JSON.stringify(msg));

        return new Promise(function(resolve){
            d.then(resolve);
        });
    }

    async a_ask(endpoint, args, timeout) {
        return this.ask(endpoint, args);
    }

    call(endpoint, args) {
        /**
         * Tell the server something has happened but don't expect a direct response.
         *
         * @type {{args: *, endpoint: *, type: string}}
         */
        let msg = {type:"call", endpoint:endpoint, args: args};
        this._sendRaw(JSON.stringify(msg));
    }

    tell(endpoint, args) {
        let msg = {type:"tell", endpoint: endpoint, args: args};
        this._sendRaw(JSON.stringify(msg));
    }

    register(endpoint, func) {
        this.endpoints[endpoint] = func
    }

}