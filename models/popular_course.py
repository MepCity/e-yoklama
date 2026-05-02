from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base


class PopularCourse(Base):
    __tablename__ = 'popular_courses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String(100), nullable=False)
    course_name = Column(String(100), nullable=False)
    course_code = Column(String(20), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
