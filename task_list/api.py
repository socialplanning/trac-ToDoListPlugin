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
                if action in controller.get_ticket_actions(req, ticket, action)]

    def render_action_control(self, req, ticket, action):
        first_label = None
        widgets = []
        hints = []
        for controller in self.controllers_for_action(req, ticket, action):
            label, widget, hint = controller.render_ticket_action_control(
                req, ticket, action)
            if first_label is None:
                first_label = label
            widgets.append(widget)
            hints.append(hint)
        return field_label, widgets, hints

    def render_action_button(self, task, action):
        if action == "leave":
            return Markup("""
              <label class="button">
                <input type="hidden" name="action" value="leave" />
                <a data-comment="required" name="act">+ Comment</a>
              </label>
""")
        if action == "reopen":
            return Markup("""
              <label class="button">
                <input type="hidden" name="action" value="reopen" />
                <input checked="checked" type="checkbox" name="act" />
                Reopen
              </label>
""")
        if action == "resolve":
            return Markup("""
              <label class="button trac-delete">
                <input type="hidden" name="action" value="resolve" />
                <input type="checkbox" name="act" />
                Close
              </label>
""")

        return Markup("""
              <label class="button">
                <input type="hidden" name="action" value="%s" />
                <a name="act" />
                %s
              </label>
""" % (action, action.title()))
        
