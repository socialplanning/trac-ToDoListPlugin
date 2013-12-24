
sentinal = object()
class TaskList(object):

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
