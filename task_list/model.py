
class TaskList(object):

    @classmethod
    def load(cls, db, slug):
        tasklist = db("SELECT id, slug, name, "
                      "created_at, created_by, "
                      "description FROM task_list "
                      "WHERE slug=%s", [slug])
        try:
            tasklist = tasklist[0]
        except IndexError:
            raise #@@TODO
        return cls(*tasklist)

    def __init__(self, id, slug, name, 
                 created_at=None, created_by=None,
                 description=None):
        self.id = int(id)
        self.slug = slug
        self.name = name

    def to_json(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            }

    def list_tickets(self, db):
        child_tickets = db("SELECT ticket, `order` "
                           "FROM task_list_child_ticket "
                           "WHERE task_list_child_ticket.task_list=%s "
                           "ORDER BY task_list_child_ticket.`order` ASC", [self.id])
        return [
            Task(self.id, ticket[0], ticket[1])
            for ticket in child_tickets
            ]

    def get_ticket(self, db, ticket):
        this_ticket = db("SELECT ticket, `order` "
                         "FROM task_list_child_ticket "
                         "WHERE task_list=%s "
                         "AND ticket=%s",
                         [self.id, ticket])
        try:
            this_ticket = this_ticket[0]
        except IndexError:
            raise #@@TODO
        return Task(self.id, this_ticket[0], this_ticket[1])

class Task(object):
    
    def __init__(self, task_list, ticket, order):
        self.task_list_id = task_list
        self.ticket_id = ticket
        self.order = order

    def to_json(self):
        return {
            'task_list': self.task_list_id,
            'ticket': self.ticket_id,
            'order': self.order,
            }

    def next(self, db):
        next_ticket = db("SELECT ticket, `order` "
                         "FROM task_list_child_ticket "
                         "WHERE task_list=%s "
                         "AND `order` > %s LIMIT 1",
                         [self.task_list_id, self.order])
        try:
            next_ticket = next_ticket[0]
        except IndexError:
            return None
        else:
            return Task(self.task_list_id, next_ticket[0], next_ticket[1])

    def prev(self, db):
        next_ticket = db("SELECT ticket, `order` "
                         "FROM task_list_child_ticket "
                         "WHERE task_list=%s "
                         "AND `order` < %s LIMIT 1",
                         [self.task_list_id, self.order])
        try:
            next_ticket = next_ticket[0]
        except IndexError:
            return None
        else:
            return Task(self.task_list_id, next_ticket[0], next_ticket[1])

