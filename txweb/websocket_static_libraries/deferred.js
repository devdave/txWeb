export {Deferred};

class Deferred {

    constructor() {
        this.cbs = [];
        this.ebs = [];
        this.fired = false;
    }

    fire(result) {
        if (this.fired == true) {

        }
        for(let pos in this.cbs) {
            let func = this.cbs[pos];
            console.log(pos, func)
            result = func(result);
        }
    }

    then(callback) {
        this.cbs.push(callback);
    }

}

