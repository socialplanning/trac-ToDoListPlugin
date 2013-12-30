from genshi.builder import tag
from pkg_resources import resource_filename
import re
from trac.core import *
from trac.util import get_reporter_id
from trac.util.translation import _
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, INavigationContributor, Chrome
from trac.web.chrome import add_stylesheet, add_script, add_script_data
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket

from task_list.api import TasklistWorkflowManager
from task_list.model import TaskList
from task_list.utils import json_dumps 

class RequestHandler(object):

    def get_csrf_token(cls, self, req):
        return {"token": req.form_token}

    def create_ticket_in_tasklist(cls, self, req):

        task_list = TaskList.load(self.env, id=req.args['tasklist_id'])

        ticket = Ticket(self.env)

        assert "field_summary" in req.args
        ticket_data = {field.split("field_")[1]: value for field, value in req.args.iteritems()
                       if field.startswith("field_")}
        ticket_data['status'] = "new"
        ticket_data['reporter'] = (req.args.get("field_reporter")
                                   or get_reporter_id(req, 'author'))
        ticket.populate(ticket_data)
        ticket.insert()

        with self.env.db_transaction as db:
            # @@TODO assert tasklist with tasklist_id exists
            # @@TODO assert ticket with id exists
            # @@TODO assert child ticket with (tasklist_id, id) does not exist
            db("INSERT INTO task_list_child_ticket "
               "  (task_list, ticket, `order`) VALUES "
               "  (%s, %s, %s)", [req.args['tasklist_id'], ticket.id, req.args['order']])

        task = task_list.get_ticket(ticket.id)
        task.actions =  TasklistWorkflowManager(self.env).allowed_actions(task_list, req, task.ticket)

        data = {
            "task_list": task_list,
            "task": task,
            "workflow_manager": TasklistWorkflowManager(self.env),
            }
        list_item = Chrome(self.env).render_template(req, 'show_tasklist_ticket.html',
                                                     data, 'text/html')
        return {"ok": "ok",
                "remove": False,
                "list_item": list_item,
                }

    def act_on_ticket(cls, self, req):
        tasklist_id = req.args['tasklist_id']
        ticket_id = int(req.args["tasklist_ticket"]) #@@TODO

        ticket = Ticket(self.env, tkt_id=ticket_id)

        task_list = TaskList.load(self.env, slug=tasklist_id)

        user_action = req.args['action']

        system = TicketSystem(self.env)

        field_changes = {}
        for controller in system.action_controllers:
            actions = [a for w, a in controller.get_ticket_actions(req, ticket)]
            if user_action not in actions:
                continue
            action_changes = controller.get_ticket_changes(req, ticket, user_action)
            field_changes.update(action_changes)

        for key, value in field_changes.items():
            ticket[key] = value
        ticket.save_changes(author=get_reporter_id(req, 'author'),
                            comment=req.args.get("comment"))

        task = task_list.get_ticket(ticket.id)
        task.actions =  TasklistWorkflowManager(self.env).allowed_actions(task_list, req, task.ticket)
            
        data = {
            "task_list": task_list,
            "task": task,
            "workflow_manager": TasklistWorkflowManager(self.env),
            }
        list_item = Chrome(self.env).render_template(req, 'show_tasklist_ticket.html',
                                                     data, 'text/html')
        return {
            "ok": "ok",
            "remove": ticket['status'] in task_list.ticket_status_blacklist,
            "list_item": list_item,
            }

    def put_ticket_in_tasklist(cls, self, req):
        tasklist_id = req.args['tasklist_id']
        ticket_id = int(req.args["tasklist_ticket"]) #@@TODO
        if 'order' in req.args:
            order = float(req.args["order"]) #@@TODO
        else:
            order = None
        
        with self.env.db_transaction as db:
            # @@TODO assert tasklist with tasklist_id exists
            # @@TODO assert ticket with id exists
            # @@TODO assert child ticket with (tasklist_id, id) does not exist

            if order is not None:
                db("INSERT INTO task_list_child_ticket "
                   "  (task_list, ticket, `order`) VALUES "
                   "  (%s, %s, %s)", [tasklist_id, ticket_id, order])
            else: # put it at the end of the list
                db("INSERT INTO task_list_child_ticket "
                   "  (task_list, ticket, `order`) VALUES "
                   "  (%s, %s, "
                   "   (SELECT MAX(`order`) + 1 "
                   "    FROM task_list_child_ticket "
                   "    WHERE task_list=%s) "
                   "  )",
                   [tasklist_id, ticket_id, tasklist_id])

        return {
            "ok": "ok",
            "tasklist": TaskList.load(self.env, id=tasklist_id).to_json(),
            }

    def show_ticket_in_tasklist(cls, self, req):
        tasklist_id = req.args['tasklist_id']
        ticket_id = int(req.args['tasklist_ticket']) #@@TODO

        task_list = TaskList.load(self.env, slug=tasklist_id)

        this_ticket = task_list.get_ticket(ticket_id)
        next_ticket = this_ticket.next()
        prev_ticket = this_ticket.prev()

        return {
            "task_list": task_list,
            "ticket": this_ticket,
            "next": next_ticket,
            "prev": prev_ticket,
            }
        
    def list_tasklists(cls, self, req):
        with self.env.db_query as db:
            resp = db("SELECT id, slug, name FROM task_list "
                      "ORDER BY name ASC")
        task_lists = []
        for row in resp:
            task_lists.append(TaskList(self.env, *row, count_tickets=True))
        return "list_tasklists.html", {"task_lists": task_lists}, None

    def show_tasklist(cls, self, req):
        tasklist_id = req.args['tasklist_id']
        
        task_list = TaskList.load(self.env, slug=tasklist_id)
        child_tickets = task_list.list_tickets()
        
        for task in child_tickets:
            task.actions =  TasklistWorkflowManager(self.env).allowed_actions(task_list, req, task.ticket)

        return "show_tasklist.html", {
            "task_list": task_list, 
            "child_tickets": child_tickets,
            "workflow_manager": TasklistWorkflowManager(self.env)}, None

    router = {
        "GET": {
            "tasklist.index": list_tasklists,
            "tasklist.show": show_tasklist,
            "tasklist.ticket": show_ticket_in_tasklist,
            "tasklist.create_ticket": get_csrf_token,
            },
        "POST":{ 
            "tasklist.ticket": put_ticket_in_tasklist,
            "tasklist.create_ticket": create_ticket_in_tasklist,
            "tasklist.act_on_ticket": act_on_ticket,
            },
        }

    def GET_index_for_ticket(self, req):
        pas

    def GET_show_for_ticket(self, req):
        pass

class TaskListPlugin(Component):
    implements(IRequestHandler, ITemplateStreamFilter,
               ITemplateProvider, INavigationContributor)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            add_stylesheet(req, "tasklist/jquery.modal.css")
            add_script(req, "tasklist/jquery.modal.min.js")
            add_stylesheet(req, "tasklist/tasklist-ticket.css")
            add_script(req, "tasklist/tasklist-ticket.js")
            add_script_data(req, {"ToDoList": {
                        "ticket": {
                            data['ticket'].id: {
                                "tasklists": [
                                tasklist.to_json() for tasklist in
                                TaskList.containing_ticket(self.env, data['ticket'].id)
                                ]
                            }}
                        }})
        return stream

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('tasklist', resource_filename(__name__, 'htdocs'))]

    """
    URLs:

    /tasklist/ => show all tasklists
    /tasklist/my-first-list/ => show the "my-first-list" tasklist and its tickets
    /tasklist/my-first-list/42/ => show ticket 42, within the "my-first-list" tasklist

    /ticket/42/tasklist/ => show the tasklist which has ticket 42 as its parent
    /ticket/42/tasklists/ => show all tasklists which contain ticket 42

    Write:

    POST /tasklist/ name=foo[&ticket=100] => create new tasklist
    POST /tasklist/42/ticket/760/ order=50 => put new ticket in tasklist
    POST /tasklist/42/ticket/ summary=foo&order=50[&...] => create new ticket and put into tasklist
    POST /tasklist/42/ => reorder tasks
    """

    # IRequestHandler methods
    def match_request(self, req):
        path = req.path_info.strip("/")
        if path.startswith("ticket") and path.endswith("tasklist"):
            path = path.split("/")
            if len(path) != 3:
                return False
            req.args['tasklist_route'] = "tasklist.show_for_ticket"
            req.args['tasklist_ticket'] = path[1]
            return True
        if path.startswith("ticket") and path.endswith("tasklists"):
            path = path.split("/")
            if len(path) != 3:
                return False
            req.args['tasklist_route'] = "tasklist.index_for_ticket"
            req.args['tasklist_ticket'] = path[1]
            return True

        if not path.startswith("tasklist"):
            return False
        path = path.split("/")
        if len(path) == 1:
            req.args['tasklist_route'] = "tasklist.index"
            return True
        if len(path) == 2:
            req.args['tasklist_route'] = "tasklist.show"
            req.args['tasklist_id'] = path[1]
            return True
        if path[2] != "ticket":
            return False
        if len(path) == 3:
            req.args['tasklist_route'] = "tasklist.create_ticket"
            req.args['tasklist_id'] = path[1]
            return True
        req.args['tasklist_route'] = "tasklist.ticket"
        req.args['tasklist_id'] = path[1]
        req.args['tasklist_ticket'] = path[3]
        if len(path) == 5:
            req.args['tasklist_route'] = "tasklist.act_on_ticket"
        return True

    def process_request(self, req):
        assert req.args.get("tasklist_route") in RequestHandler.router[req.method]

        handler = RequestHandler.router[req.method][req.args.get("tasklist_route")]
        resp = handler(RequestHandler, self, req)
        if isinstance(resp, dict):
            req.send(json_dumps(resp))
        else:
            return resp


    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'tasklist'

    def get_navigation_items(self, req):
        yield ('mainnav', 'tasklist',
               tag.a(_('Task Lists'), href=req.href.tasklist()) )
        
