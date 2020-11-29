
export {ResilientSocket};
import {Deferred} from "./deferred.js";

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
    }

    connect() {

        if(this.retries > this.retryLimit) {
            console.error("Number of connect retries reached limit!");
            // TODO add a on_timeout or on_limit hook so the application can handle
            // connection retries failing.
        }

        console.debug("connecting resilient");
        this.socket = new WebSocket(this.conString);
        this.socket.addEventListener("message", this.receiveMsg.bind(this));
        this.socket.addEventListener("close", this.onclose.bind(this));
        this.socket.addEventListener("open", this.onopen.bind(this));
        this.socket.addEventListener("error", this.onerror.bind(this));
    }

    onopen() {
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

    _sendRaw(msg) {
        //Check if disconnected
        if(this.closed == true) {
            this.connect();
            this.first_open( x=>this.socket.send(msg));
        } else {
            this.socket.send(msg);
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
            console.debug(msg);
        }

        let data = JSON.parse(msg.data);
        if (data['type'] == "response") {
            let d = this.pending[data['caller_id']];
            d.fire(data.result);
            delete this.pending[data['caller_id']];
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