
$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#messageform").live("submit", function() {
        newMessage($(this));
        return false;
    });
    $("#messageform").live("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this));
            return false;
        }
    });
    $("#message").select();
    updater.start();
});

function newMessage(form) {
    var message = form.formToDict();
   
    
    updater.socket.send(JSON.stringify(message));
    form.find("input[type=text]").val("").select();
}

jQuery.fn.formToDict = function() {
    
    var fields = this.serializeArray();
    //alert(JSON.stringify(fields))
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
   // alert(JSON.stringify(json))
    return json;
};

var updater = {
    socket: null,
    //var url = "ws://" + location.host + "/chatsocket";
    //socket = new WebSocket(url);

    start: function() {
        var url = "ws://" + location.host + "/chatsocket";
        updater.socket = new WebSocket(url);

        updater.socket.onmessage = function(event) {
            updater.showMessage(JSON.parse(event.data));
        }
    },

    showMessage: function(message) {

        var $user = $('#user');
        $user.attr("class", 'label label-info');
        $user.text(message.current_user);
  
        var $user = $('#loginned_users');
        $user.attr("class", 'label label-info');
        $user.hide();
        $user.fadeIn("slow");
        $user.text(message.logined_users);
  
        
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var node = $(message.html); 
        node.hide();
        $("#inbox").append(node);
        node.slideDown();

    }
};
