
var chat_login_index  = {
    extend: 'Ext.window.Window'
    , singleton: true
    , alias: "widget.userLogin"

    , height: 150
    , width: 276
    , layout: {
        type: 'fit'
    }
    , title: 'Login'
    , modal: true
    , hidden: false

    , initComponent: function() {
        var me = this;

        me.addEvents(
            'login'
        );

        Ext.applyIf(me, {
            items: [
                {
                    xtype: 'form'
                    , layout: {
                        align: 'stretch'
                        , type: 'vbox'
                    }
                    , bodyPadding: 10
                    , title: ''
                    , url: "login"
                    , items: [
                        {
                            html: "What's your name stranger?"
                            , margin: "auto auto 5 auto"
                        }
                        ,{
                            xtype: 'textfield'
                            , name: "name"
                            , fieldLabel: 'Name'
                            , allowBlank:false
                        }
                    ]
                    , buttons: [{
                        text: "Submit"
                        , formBind:true
                        , handler: function() {
                            var myForm = this.up("form").getForm();

                            if ( myForm.isValid() ) {

                                myForm.submit({
                                    success: function(form, action) {
                                        console.log(this, form, action);
                                        if (action.result.success === true) {
                                            me.fireEvent("login", action.result);
                                        } else {

                                        }


                                    },
                                    failure: function(form, action) {
                                        console.log(this, form, action);
                                    }
                                })
                            }

                            console.log(myForm);
                        }
                    }]
                }
            ]
        });

        me.callParent(arguments);
    }
}

Ext.define("chat.view.login.Index", chat_login_index );