class TaskList(object):

    @classmethod
    def load(cls, env, slug=None, id=None):
        with env.db_query as db:
            if slug:
                tasklist = db("SELECT id, slug, name, "
                              "created_at, created_by, "
                              "description FROM task_list "
                              "WHERE slug=%s", [slug])
            else:
                tasklist = db("SELECT id, slug, name, "
                              "created_at, created_by, "
                              "description FROM task_list "
                              "WHERE id=%s", [id])
        try:
            tasklist = tasklist[0]
        except IndexError:
            raise #@@TODO
        return cls(env, *tasklist)

    def count_tickets(self):
        sql, params = self._ticket_status_blacklist_sql()
        with self.env.db_query as db:
            for ticket_count, in db("SELECT count(distinct ticket.id) "
                                    "FROM task_list_child_ticket JOIN ticket "
                                    "ON ticket.id=task_list_child_ticket.ticket "
                                    "WHERE %s "
                                    "AND task_list=%%s " % sql, params + [self.id]):
                return ticket_count

    def __init__(self, env, id, slug, name, 
                 created_at=None, created_by=None,
                 description=None, count_tickets=False):
        self.env = env

        self.id = int(id)
        self.slug = slug
        self.name = name
        if count_tickets:
            self.active_tickets = self.count_tickets() or 0
        else:
            self.active_tickets = None
        self._ticket_workflow_actions = {
            "closed": "reopen",
            "*": "resolve",
            }

    def to_json(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'active_tickets': self.active_tickets
           } 

    def get_action_for_ticket(self, req, ticket):
        return self._ticket_workflow_actions.get(ticket['status']) or \
            self._ticket_workflow_actions['*']

    @property
    def ticket_status_blacklist(self):
        return ["reopened"]

    def _ticket_status_blacklist_sql(self):
        sql = []
        params = []
        for status in self.ticket_status_blacklist:
            sql.append("status <> %s")
            params.append(status)
        return " AND ".join(sql), params

    def list_tickets(self):
        sql, params = self._ticket_status_blacklist_sql()
        child_tickets = self.env.db_query("SELECT ticket, `order` "
                           "FROM task_list_child_ticket JOIN ticket "
                           "ON ticket.id=task_list_child_ticket.ticket "
                           "WHERE %s "
                           "AND task_list_child_ticket.task_list=%%s "
                           "ORDER BY task_list_child_ticket.`order` ASC" % sql, 
                           params + [self.id])
        return [
            Task(self, ticket[0], ticket[1])
            for ticket in child_tickets
            ]

    def get_ticket(self, ticket):
        this_ticket = self.env.db_query("SELECT ticket, `order` "
                         "FROM task_list_child_ticket "
                         "WHERE task_list=%s "
                         "AND ticket=%s",
                         [self.id, ticket])
        try:
            this_ticket = this_ticket[0]
        except IndexError:
            raise #@@TODO
        return Task(self, this_ticket[0], this_ticket[1])

class Task(object):
    
    def __repr__(self):
        return u'<Task (ticket %s) in TaskList %s>' % (
            self.ticket_id, self.task_list.slug)

    def __init__(self, task_list, ticket, order):
        self.task_list = task_list
        self.ticket_id = ticket
        self.order = order

    def to_json(self):
        return {
            'task_list': self.task_list.id,
            'ticket': self.ticket_id,
            'order': self.order,
            }

    def next(self):
        sql, params = self.task_list._ticket_status_blacklist_sql()
        for ticket in self.task_list.env.db_query(
            "SELECT ticket, `order` "
            "FROM task_list_child_ticket JOIN ticket "
            "ON ticket.id=task_list_child_ticket.ticket "
            "WHERE %s "
            "AND task_list=%%s "
            "AND `order` > %%s LIMIT 1" % sql, params + [
                self.task_list.id, self.order]):
            return Task(self.task_list, *ticket)
        return None

    def prev(self):
        sql, params = self.task_list._ticket_status_blacklist_sql()
        for ticket in self.task_list.env.db_query(
            "SELECT ticket, `order` "
            "FROM task_list_child_ticket JOIN ticket "
            "ON ticket.id=task_list_child_ticket.ticket "
            "WHERE %s "
            "AND task_list=%%s "
            "AND `order` < %%s LIMIT 1" % sql, params + [
                self.task_list.id, self.order]):
            return Task(self.task_list, *ticket)
        return None

