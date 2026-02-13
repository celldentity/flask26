class Member:
    def __init__(self, id, uid, pw, name, role="user", active=True, created_at=None):
        self.id = id
        self.uid = uid
        self.pw = pw
        self.name = name
        self.role = role
        self.active = active
        self.created_at = created_at

    @classmethod
    def from_db(cls, row: dict):
        if not row:
            return None
        return cls(
            id=row.get('id'),
            uid=row.get('uid'),
            pw=row.get('password'),
            name=row.get('name'),
            role=row.get('role'),
            active=bool(row.get('active')),
            created_at=row.get('created_at')
        )

    def is_admin(self):
        return self.role == "admin"