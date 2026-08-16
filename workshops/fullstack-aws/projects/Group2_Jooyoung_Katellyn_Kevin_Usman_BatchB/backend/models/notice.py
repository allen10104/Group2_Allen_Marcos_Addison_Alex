from backend.models.category import Category

'''
A notice is a message posted to the notice board. It has a title, date, content, and category.

The validate method checks if the title, content, and category are valid.
The __init__ method initializes the notice.
The __str__ method returns a string representation of the notice.
The __repr__ method returns a string representation of the notice.
The __eq__ method checks if the notice is equal to another notice.
'''
class Notice:
    MAX_CONTENT_LENGTH = 500

    def __init__(self, id, title, date, content, category):
        self.validate(title, content, category)
        self.id = id
        self.title = title.strip()
        self.date = date
        self.content = content.strip()
        self.category = category
        # Stamped by NoticeBoard.add_notice from the actor. Do not set these yourself.
        self.author = None
        self.author_id = None

    @staticmethod
    def validate(title, content, category):
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Title is required")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content is required")
        if len(content.strip()) > Notice.MAX_CONTENT_LENGTH:
            raise ValueError(f"Content must be at most {Notice.MAX_CONTENT_LENGTH} characters")
        if not isinstance(category, Category):
            raise ValueError("Category must be a Category")

    def __str__(self):
        return (
            f"[{self.id}] {self.title} by {self.author} "
            f"({self.date}): {self.content} [{self.category.value}]"
        )

    def __repr__(self):
        return (
            f"Notice(id={self.id}, title={self.title}, date={self.date}, "
            f"author={self.author}, author_id={self.author_id}, "
            f"content={self.content}, category={self.category})"
        )

    def __eq__(self, other):
        if not isinstance(other, Notice):
            return False
        return self.id == other.id
