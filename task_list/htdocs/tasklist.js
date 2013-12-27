jQuery(document).ready(function($) {
  var
      form = $("#tasklist-newticket"),
      end_of_line = (parseFloat( $("#tasklist > li[data-order]:last").data("order") ) + 1) || 0;

  form.find("input[name=order], input[type=submit]").hide();
  form.find("input[name=order]").val( end_of_line );
  
  $("#tasklist").on("mouseover", "li:not(#tasklist-newticket)", function() {
    $(this).append("<a href='#' class='plus'>&#43;</a>");
  });
  $("#tasklist").on("mouseout", "li:not(#tasklist-newticket)", function() {
    $(this).find(".plus").remove();
  });
  $("#tasklist").on("click", "li:not(#tasklist-newticket)", function() {
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
    $(form).insertAfter(this);
  });
  $("#tasklist").on("click", ".act", function() {
    var li = $(this).closest("li"),
        href = li.find("a.ticket").attr("href");
    $.post(href).done(function(resp) { resp = JSON.parse(resp); if( resp.remove ) { li.remove(); }});
    return false;
  });
  $("#tasklist").on("click", "a.ticket", function() {
    var href = $(this).attr("href") + "/act";
    $.get($(this).data("ticket-href"), function(html) { 
      $.get(href, function(json) {
        json = JSON.parse(json);
        var container = $("<div>").html(html);
        $("body").remove("#ticket-container");
        var new_container = $("<div>").attr("id", "ticket-container"),
            header = "<div class='tasklist-nav nav'><ul>";
/*        if( json.prev ) {
          header += "<li class='first'><a rel='prev' href='#'>Previous</a></li>";
        }
        if( json.next ) {
          header += "<li class='last'><a rel='next' href='#'>Next</a></li>";
        }
        header += "</ul></div>";
*/
        new_container.html(header);
        container.find("#ticket").appendTo(new_container);
        new_container.appendTo("body").modal();
      });
    });
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
      var li = $("<li><span class='act'>!</span></li>").attr("data-order", resp.order);
      var a = $("<a>").addClass("ticket")
               .attr("data-ticket-href", resp.ticket_href)
               .attr("href", resp.href).text(resp.values.summary).appendTo(li);
      li.insertBefore(form);
    });
    $(form).find("input[name=field_summary]").val("");
    return false;
  });
});
