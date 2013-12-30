import json

class TaskList(object):

    @classmethod
    def containing_ticket(cls, env, ticket_id):
        with env.db_query as db:
            tasklists = db("SELECT DISTINCT id, slug, name, "
                           "created_at, created_by, "
                           "description, configuration "
                           "FROM task_list "
                           "JOIN task_list_child_ticket child "
                           " ON child.task_list=task_list.id "
                           "WHERE child.ticket=%s", [ticket_id])
        return [TaskList(env, *tasklist) for tasklist in tasklists]

    @classmethod
    def load(cls, env, slug=None, id=None):
        with env.db_query as db:
            if slug:
                tasklist = db("SELECT id, slug, name, "
                              "created_at, created_by, "
                              "description, configuration "
                              "FROM task_list "
                              "WHERE slug=%s", [slug])
            else:
                tasklist = db("SELECT id, slug, name, "
                              "created_at, created_by, "
                              "description, configuration "
                              "FROM task_list "
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
                 description=None, configuration=None,
                 count_tickets=False):
        self.env = env

        self.id = int(id)
        self.slug = slug
        self.name = name

        self.configuration = None
        if configuration is not None:
            self.configuration = json.loads(configuration)

        self.active_tickets = None
        if count_tickets:
            self.active_tickets = self.count_tickets() or 0

    def to_json(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'active_tickets': self.active_tickets
           } 

    def get_all_actions(self):
        return ["resolve", "reopen", "leave"]

    def render_action(self, action):
        from genshi.core import Markup
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

    @property
    def ticket_status_blacklist(self):
        statuses = None
        if self.configuration:
            statuses = self.configuration.get("ticket_status_blacklist")
        if statuses is None:
            statuses = ["closed"]
        return statuses

    @property
    def css(self):
        return """
li[data-status=closed] a {
  font-style: italic;
  text-decoration: line-through;
}
"""

    def _ticket_status_blacklist_sql(self):
        sql = []
        params = []
        for status in self.ticket_status_blacklist:
            sql.append("status <> %s")
            params.append(status)
        return " AND ".join(sql), params

    def list_tickets(self):
        sql, params = self._ticket_status_blacklist_sql()
        child_tickets = self.env.db_query(
            "SELECT child.ticket, child.`order`, parent.task_list "
            "  FROM task_list_child_ticket child "
            " JOIN ticket ON ticket.id=child.ticket "
            " LEFT JOIN task_list_parent_ticket parent "
            "   ON parent.ticket=child.ticket "
            "WHERE %s "
            "AND child.task_list=%%s "
            "ORDER BY child.`order` ASC" % sql, 
            params + [self.id])
        return [
            Task(self, *ticket)
            for ticket in child_tickets
            ]

    def get_ticket(self, ticket):
        this_ticket = self.env.db_query(
            "SELECT child.ticket, `order`, parent.task_list "
            "FROM task_list_child_ticket child"
            " LEFT JOIN task_list_parent_ticket parent "
            "   ON parent.ticket=child.ticket "
            "WHERE child.task_list=%s "
            "AND child.ticket=%s",
            [self.id, ticket])
        try:
            this_ticket = this_ticket[0]
        except IndexError:
            raise #@@TODO
        return Task(self, *this_ticket)

class Task(object):
    
    def __repr__(self):
        return u'<Task (ticket %s) in TaskList %s>' % (
            self.ticket_id, self.task_list.slug)

    def __init__(self, task_list, ticket, order, sub_task_list=None):
        self.task_list = task_list
        self.ticket_id = ticket
        self.order = order
        self.sub_task_list = None
        if sub_task_list is not None:
            self.sub_task_list = TaskList.load(task_list.env, id=sub_task_list)
        self.ticket = None

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

