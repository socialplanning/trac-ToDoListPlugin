from genshi.builder import tag
from genshi.core import Markup
from trac.ticket.api import TicketSystem
from trac.core import Component

class TasklistWorkflowManager(Component):

    @property
    def action_controllers(self):
        return TicketSystem(self.env).action_controllers

    def allowed_actions(self, task_list, req, ticket):
        allowed = task_list.get_all_actions()
        return [action for action in 
                TicketSystem(self.env).get_available_actions(req, ticket)
                if action in allowed]

    def controllers_for_action(self, req, ticket, action):
        return [controller for controller in self.action_controllers
                if action in [i[1] for i in controller.get_ticket_actions(req, ticket)]]

    def render_action_control(self, req, ticket, action):
        first_label = None
        widgets = []
        hints = []
        for controller in self.controllers_for_action(req, ticket, action):
            print controller, action
            label, widget, hint = controller.render_ticket_action_control(
                req, ticket, action)
            if first_label is None:
                first_label = label
            widgets.append(widget)
            hints.append(hint)
        return first_label, tag(*widgets), (hints and '. '.join(hints) or '')

    def render_action_button(self, req, task, action):
        markup = None
        if action == "leave":
            markup = """
              <label class="button">
                <input type="hidden" name="action" value="leave" />
                <a data-comment="required" name="act">+ Comment</a>
"""
        if action == "reopen":
            markup = """
              <label class="button">
                <input type="hidden" name="action" value="reopen" />
                <input checked="checked" type="checkbox" name="act" />
                Reopen
"""
        if action == "resolve":
            markup = """
              <label class="button trac-delete">
                <input type="hidden" name="action" value="resolve" />
                <input type="checkbox" name="act" />
                Close
"""

        if markup is None:
            markup = """
              <label class="button">
                <input type="hidden" name="action" value="%s" />
                <a name="act">%s</a>
""" % (action, action.title())
        
        supplemental_form = ""
        label, widgets, hints = self.render_action_control(req, task.ticket, action)
        if widgets.children:
            supplemental_form = "<div class='supplemental'><div class='supplemental-form'>%s %s <span class='hint'>%s</span><textarea style='width:95%%' rows='5' name='comment' placeholder='Enter your comment'></textarea><input type='submit' /></div></div>" % (action.title(), str(widgets), hints)
        markup = markup + supplemental_form + "</label>"
        return Markup(markup)
