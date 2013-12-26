jQuery(document).ready(function($) {
//  var
      form = $("#tasklist-newticket"),
      end_of_line = parseFloat( $("#tasklist > li[data-order]:last").data("order") ) + 1;

  form.find("input[name=order], input[type=submit]").hide();
  form.find("input[name=order]").val( end_of_line );
  
  $("#tasklist > li:not(#tasklist-newticket)").on("mouseover", function() {
    $(this).append("<a href='#' class='plus'>&#43;</a>");
  }).on("mouseout", function() {
    $(this).find(".plus").remove();
  }).on("click", function() {
    var this_pos = parseFloat($(this).closest("li:not(#tasklist-newticket)").data("order")),
        next_pos = parseFloat($(this).closest("li").next("li:not(#tasklist-newticket)").data("order")),
        new_pos = null;
    if( isNaN(next_pos) ) {
      new_pos = this_pos + 1;
    } else {
      new_pos = (this_pos + next_pos) / 2.0;
    }
    $(form).find("input[name=order]").val(new_pos);
    window.setTimeout(function() { $(form).find("input[name=field_summary]").focus(); }, 0);
    $(form).insertAfter(this);
  }).find("a.ticket").on("click", function() {
    $.get($(this).data("ticket-href"), function(html) { 
      var container = $("<div>").html(html);
      $("body").remove("#ticket");
      container.find("#ticket").appendTo("body").modal();
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
      var li = $("<li>").attr("data-order", resp.order);
      var a = $("<a>").addClass("ticket").attr("href", resp.href).text(resp.values.summary).appendTo(li);
      li.insertBefore(form);
    });
    $(form).find("input[name=field_summary]").val("");
    return false;
  });
});
