jQuery(document).ready(function($) {
  var
      form = $("#tasklist-newticket"),
      end_of_line = (parseFloat( $("#tasklist > li[data-order]:last").data("order") ) + 1) || 0;

  form.find("input[name=order], input[type=submit]").hide();
  form.find("input[name=order]").val( end_of_line );
  
  $("#tasklist").on("click", "input[name=add]", function() {
console.log(this);
    var this_pos = parseFloat($(this).closest("li:not(#tasklist-newticket)").data("order")),
        next_pos = parseFloat($(this).closest("li").next("li:not(#tasklist-newticket)").data("order")),
        new_pos = null;
    if( isNaN(next_pos) ) {
      new_pos = this_pos + 1;
    } else {
      new_pos = (this_pos + next_pos) / 2.0;
    }
console.log(this_pos, next_pos, new_pos);
    $(form).find("input[name=order]").val(new_pos);
    window.setTimeout(function() { $(form).find("input[name=field_summary]").focus(); }, 0);
    $(form).insertAfter($(this).closest("li"));
  });
  $("#tasklist").on("click", "input[name=act]", function(evt) {
    var commentBefore = evt.altKey,
        showAfter = evt.shiftKey,
        li = $(this).closest("li"),
        href = li.find("a.ticket").attr("href"),
        ticket_href = li.find("a.ticket").data("ticket-href");
      
    if( commentBefore ) {
        var container = $("<div>").html("<form><textarea style='width:95%' rows='5' name='comment' placeholder='Enter your comment'></textarea><input type='submit' style='margin-left: 90%' value='Go' /></form>");
        container.find("form").on("submit", function() {

            $.post(href, ticket_href, showAfter, li, 
                   { comment: container.find("form [name=comment]").val() });
            $.modal.close();
            return false;
        });
        container.appendTo("body").modal();
        window.setTimeout(function() { container.find("form [name=comment]").focus(); }, 0);
    } else {
      actOnTicket(href, ticket_href, li, showAfter);
    }
    return false;
  });

  function actOnTicket(href, ticket_href, li, showAfter, data) {
    data = data || {};
    data['__FORM_TOKEN'] = $("[name=__FORM_TOKEN]").val();
    $.post(href, data).done(function(resp) { 
        resp = JSON.parse(resp); 
        if( resp.remove ) { 
            li.remove(); 
        } else {
            li.replaceWith(resp.list_item);
        }
        if( showAfter ) {
            showModalTicket(ticket_href);
        }
    });
    return false;
  };

  function showModalTicket(href) {
    $.get(href, function(html) { 
        var container = $("<div>").html(html);
        $("body").remove("#ticket-container");
        var new_container = $("<div>").attr("id", "ticket-container"),
            header = "<div class='tasklist-nav nav'><ul>";
        new_container.html(header);
        container.find("#ticket").appendTo(new_container);
        new_container.appendTo("body").modal();
    });      
  };

  $("#tasklist").on("click", "a.ticket", function() {
    var href = $(this).data("ticket-href");
    showModalTicket(href);
    return false;
  });

  $(form).find("input[name=field_summary]").on("keypress", function(e) {
    if( e.which === 13 ) {
      $(this).closest("form").submit();
    }
  });

  $(form).find("form").on("submit", function() {
    var data = $(this).serialize();
    $.post($(this).attr("action"), data).done(function(resp) {
      resp = JSON.parse(resp);
      var li = $("<li class='tasklist-ticket'><div class='inlinebuttons'><input type='button' name='add' value='+ Ticket' /><input type='button' name='act' class='trac-delete' value='Act!' /></div></li>").attr("data-order", resp.order);
      var a = $("<a>").addClass("ticket")
               .attr("data-ticket-href", resp.ticket_href)
               .attr("href", resp.href).text(resp.values.summary).prependTo(li);
      li.insertBefore(form);
    });
    $(form).find("input[name=field_summary]").val("");
    return false;
  });
});
