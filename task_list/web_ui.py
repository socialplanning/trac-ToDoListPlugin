from genshi.builder import tag
from pkg_resources import resource_filename
import re
from trac.core import *
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, Chrome

from task_list.model import TaskList
from task_list.utils import json_dumps 

class RequestHandler(object):

    def show_ticket_in_tasklist(cls, self, req):
        tasklist_id = req.args['tasklist_id']
        ticket_id = int(req.args['tasklist_ticket'])

        with self.env.db_query as db:
            tasklist = db("SELECT id, slug, name, "
                          "created_at, created_by, "
                          "description FROM task_list "
                          "WHERE slug=%s", [tasklist_id])
            try:
                task_list = TaskList(*tasklist[0])
            except IndexError:
                raise #@@TODO

            this_ticket = db("SELECT `order` "
                             "FROM task_list_child_ticket "
                             "WHERE task_list=%s "
                             "AND ticket=%s",
                             [task_list.id, ticket_id])
            try:
                this_ticket = this_ticket[0]
            except IndexError:
                raise #@@TODO

            this_ticket_position = this_ticket[0]
            next_ticket = db("SELECT ticket "
                             "FROM task_list_child_ticket "
                             "WHERE task_list=%s "
                             "AND `order` > %s LIMIT 1",
                             [task_list.id, this_ticket_position])
            try:
                next_ticket = next_ticket[0]
            except IndexError:
                next_ticket = None
            last_ticket = db("SELECT ticket "
                             "FROM task_list_child_ticket "
                             "WHERE task_list=%s "
                             "AND `order` < %s LIMIT 1",
                             [task_list.id, this_ticket_position])
            try:
                last_ticket = last_ticket[0]
            except IndexError:
                last_ticket = None
        return {
            "task_list": tasklist,
            "ticket": this_ticket,
            "next": next_ticket,
            "prev": last_ticket,
            }
        
    def list_tasklists(cls, self, req):
        with self.env.db_query as db:
            resp = db("SELECT id, slug, name FROM task_list "
                      "ORDER BY name ASC")
        task_lists = []
        for row in resp:
            task_lists.append(TaskList(*row))
        return {"task_lists": task_lists}

    def show_tasklist(cls, self, req):
        tasklist_id = req.args['tasklist_id']
        
        with self.env.db_query as db:
            tasklist = db("SELECT id, slug, name, "
                          "created_at, created_by, "
                          "description FROM task_list "
                          "WHERE slug=%s", [tasklist_id])
            try:
                task_list = TaskList(*tasklist[0])
            except IndexError:
                raise #@@TODO

            child_tickets = db("SELECT id, summary "
                               "FROM ticket "
                               "JOIN task_list_child_ticket "
                               "ON ticket.id=task_list_child_ticket.ticket "
                               "WHERE task_list_child_ticket.task_list=%s "
                               "ORDER BY task_list_child_ticket.`order` ASC", [task_list.id])
        return {"task_list": task_list, 
                "child_tickets": list(child_tickets)}

    router = {
        "GET": {
            "tasklist.index": list_tasklists,
            "tasklist.show": show_tasklist,
            "tasklist.ticket": show_ticket_in_tasklist,
            },
        "POST": {
            
            },
        }

    def GET_index_for_ticket(self, req):
        pass

    def GET_show_for_ticket(self, req):
        pass

class TaskListPlugin(Component):
    implements(IRequestHandler, ITemplateProvider, INavigationContributor)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('pastebin', resource_filename(__name__, 'htdocs'))]

    """
    URLs:

    /tasklist/ => show all tasklists
    /tasklist/my-first-list/ => show the "my-first-list" tasklist and its tickets
    /tasklist/my-first-list/42/ => show ticket 42, within the "my-first-list" tasklist

    /ticket/42/tasklist/ => show the tasklist which has ticket 42 as its parent
    /ticket/42/tasklists/ => show all tasklists which contain ticket 42
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
        if len(path) != 4 or path[2] != "ticket":
            return False
        req.args['tasklist_route'] = "tasklist.ticket"
        req.args['tasklist_id'] = path[1]
        req.args['tasklist_ticket'] = path[3]
        return True

    def process_request(self, req):
        assert req.args.get("tasklist_route") in RequestHandler.router[req.method]

        handler = RequestHandler.router[req.method][req.args.get("tasklist_route")]
        resp = handler(RequestHandler, self, req)
        req.send(json_dumps(resp))


    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'tasklist'

    def get_navigation_items(self, req):
        yield ('mainnav', 'tasklist',
               tag.a(_('Task Lists'), href=req.href.list()) )
        
