jQuery(document).ready(function($) {
    $("<input>").attr("type", "submit").attr("name", "add_to_tasklist")
        .attr("value", "+ Add to Tasklist")
        .on("click", promptAddToTasklist)
        .appendTo("#ticket .inlinebuttons");
    
    function promptAddToTasklist() {
        var ticket = parseInt($("#ticket a.trac-id").text().substr(1));
        $.get("../tasklist/", function(data) { /* @@TODO: better url generation */
            data = $("<div>").html(data).find("#content");
            var tasklists = ToDoList.ticket[ticket].tasklists;
            for( var i=0; i<tasklists.length; ++i ) {
                $(data).find("li[data-tasklist-slug="+tasklists[i].slug+"]").remove();
            }
            $("<div>").html(data.html()).on("click", "a", selectAddToTasklist)
                .appendTo("body").modal();
        });
        return false;
    };

    function selectAddToTasklist() {
        var tasklist = $(this).data("tasklist-id");
        var ticket = parseInt($("#ticket a.trac-id").text().substr(1));
        $.post("../tasklist/"+tasklist+"/ticket/"+ticket, {
            "__FORM_TOKEN": $("[name=__FORM_TOKEN]").val() })
            .done(function(data) { 
                data = JSON.parse(data);
                if( data.ok == "ok" ) {
                    ToDoList.ticket[ticket].tasklists.push(data.tasklist);
                    initTasklists();
                }
            });
        $.modal.close();
        return false;
    };

    function initTasklists() {
        var ticket = parseInt($("#ticket a.trac-id").text().substr(1)),
            tasklists = ToDoList.ticket[ticket].tasklists,
            container = $("#content.ticket .trac-topnav span.ticket-tasklists");
        if( container.length != 0 ) { 
            container.remove();
        }
        container = $("<span>").addClass("ticket-tasklists")
            .css("float", "left").text("View in task list: ");
        for( var i=0; i<tasklists.length; ++i ) {
            $("<a>").attr("href", "../tasklist/"+tasklists[i].slug)
                .text(tasklists[i].name)
                .appendTo(container);
        }
        if( tasklists.length != 0 ) {
            container.appendTo("#content.ticket .trac-topnav");
        }
    };

    initTasklists();
});
