Ext.Loader.setConfig({
        enabled : true,
        paths   : {
            app : 'app/chat'
            , chat: 'app/chat'
        }
    });
Ext.require("chat.view.login.Index");

Ext.application({
    name: 'chat'
    , appFolder: "app/chat"
    , controllers: [
        //'Login',
        'Home'
    ]
    , views: [
        'chat.view.login.Index'
    ]
    //, autoCreateViewport: false

    , launch: function() {
        chat.view.login.Index.on("login", this.onLoggedIn, this);
        chat.view.login.Index.show()
    }
    , onLoggedIn: function(results) {
        console.log(arguments)
        Ext.Msg.alert("Howdy", JSON.stringify( results) )
    }
});